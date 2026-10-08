# Copyright 2026 Verified JSON contributors
# SPDX-License-Identifier: Apache-2.0
import errno
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "verification"))
import process_runner
from process_runner import run_bounded


@unittest.skipUnless(os.name == "posix" and hasattr(os, "WNOWAIT"), "requires POSIX waitid(WNOWAIT)")
class BoundedProcessTests(unittest.TestCase):
    def setUp(self):
        work = os.environ.get("VERIFIED_JSON_TEST_WORK")
        if not work or not Path(work).is_dir():
            raise RuntimeError("Set VERIFIED_JSON_TEST_WORK to an allocated existing test scratch directory")
        self.tmp = tempfile.TemporaryDirectory(dir=work)
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")

    def run_code(self, code, **kwargs):
        return run_bounded([sys.executable, "-B", "-c", code], cwd=self.root,
                           env=self.env, timeout=kwargs.pop("timeout", 2), **kwargs)

    def assert_clean(self, result, code=0):
        self.assertEqual(result.returncode, code, result)
        self.assertFalse(result.timed_out, result)
        self.assertFalse(result.output_limited, result)
        self.assertIsNone(result.cleanup_error, result)

    def test_success_and_nonzero_preserve_binary_streams(self):
        for code in (0, 7):
            result = self.run_code(
                f"import os; os.write(1, b'out\\xff\\n'); os.write(2, b'err\\xfe\\n'); raise SystemExit({code})")
            self.assert_clean(result, code)
            self.assertEqual(result.group_cleanup, "not_attempted_normal_exit")
            self.assertTrue(result.direct_child_reaped)
            self.assertEqual(result.stdout, b"out\xff\n")
            self.assertEqual(result.stderr, b"err\xfe\n")

    def test_merged_stderr(self):
        result = self.run_code("import os; os.write(1,b'one'); os.write(2,b'two')", merge_stderr=True)
        self.assert_clean(result)
        self.assertEqual(result.stdout, b"onetwo")
        self.assertEqual(result.stderr, b"")

    def test_missing_executable_is_infrastructure(self):
        result = run_bounded([str(self.root / "no-executable")], cwd=self.root, env=self.env, timeout=1)
        self.assertIsNone(result.returncode)
        self.assertIn("spawn failed", result.cleanup_error)
        self.assertFalse(result.timed_out)
        self.assertEqual(result.stdout, b"")
        self.assertEqual(result.group_cleanup, "not_attempted")
        self.assertFalse(result.direct_child_reaped)

    def test_timeout_preserves_both_partial_diagnostics(self):
        result = self.run_code("import os,time; os.write(1,b'partial-out'); os.write(2,b'partial-err'); time.sleep(5)",
                               timeout=0.15)
        self.assertTrue(result.timed_out)
        self.assertEqual(result.returncode, -signal.SIGKILL)
        self.assertIsNone(result.cleanup_error)
        self.assertEqual(result.stdout, b"partial-out")
        self.assertEqual(result.stderr, b"partial-err")
        self.assertLess(result.duration_seconds, 1.5)
        self.assertEqual(result.group_cleanup, "signaled_owned_group")
        self.assertTrue(result.direct_child_reaped)

    def test_deadline_includes_child_after_pipe_eof(self):
        result = self.run_code("import os,time; os.close(1); os.close(2); time.sleep(5)", timeout=0.15)
        self.assertTrue(result.timed_out)
        self.assertEqual(result.returncode, -signal.SIGKILL)
        self.assertEqual(result.group_cleanup, "signaled_owned_group")
        self.assertTrue(result.direct_child_reaped)
        self.assertLess(result.duration_seconds, 1.5)

    def test_flood_is_bounded_across_both_streams(self):
        result = self.run_code("import os\nwhile True:\n os.write(1,b'x'*4096)\n os.write(2,b'y'*4096)",
                               output_limit=32768)
        self.assertTrue(result.output_limited, result)
        self.assertEqual(len(result.stdout) + len(result.stderr), 32768)
        self.assertFalse(result.timed_out)
        self.assertEqual(result.returncode, -signal.SIGKILL)

    def test_exact_output_cap_and_zero_output_cap(self):
        result = self.run_code("import os; os.write(1,b'x'*8192)", output_limit=8192)
        self.assert_clean(result)
        self.assertEqual(len(result.stdout), 8192)
        self.assert_clean(self.run_code("pass", output_limit=0))
        self.assertTrue(self.run_code("print('x')", output_limit=0).output_limited)

    def test_detached_inherited_pipes_do_not_extend_deadline_to_eof(self):
        done = self.root / "detached-done"
        code = f"""import os,time
r,w=os.pipe()
pid=os.fork()
if pid == 0:
    os.close(r)
    os.setsid()
    os.write(2,b'detached-ready')
    os.write(w,b'1')
    os.close(w)
    time.sleep(0.9)
    with open({str(done)!r},'w') as stream:
        stream.write('done')
    os._exit(0)
os.close(w)
os.read(r,1)
os.close(r)
os.write(1,b'leader-done')
"""
        result = self.run_code(code, cleanup_seconds=0.05)
        self.assertEqual(result.returncode, 0)
        self.assertFalse(result.timed_out)
        self.assertIn("pipe EOF not established", result.cleanup_error)
        self.assertEqual(result.stdout, b"leader-done")
        self.assertEqual(result.stderr, b"detached-ready")
        self.assertLess(result.duration_seconds, 0.7)
        self.assertIn(result.group_cleanup, {"signaled_owned_group", "uncertain"})
        self.assertTrue(result.direct_child_reaped)
        # Benign escaped fixture terminates itself; never hunt or signal an
        # unowned process group. Wait only for its private completion marker.
        deadline = time.monotonic() + 3
        while not done.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertTrue(done.exists(), "self-exiting detached fixture did not complete")

    def test_group_signal_happens_while_leader_is_unreaped(self):
        real_killpg, real_wait = os.killpg, subprocess.Popen.wait
        events = []

        def killpg(pid, sig):
            observed = os.waitid(os.P_PID, pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
            self.assertIsNotNone(observed, "fast fixture should already be observed as exited")
            self.assertEqual(observed.si_pid, pid)
            events.append(("signal", pid))
            return real_killpg(pid, sig)

        def wait(process, *args, **kwargs):
            self.assertIn(("signal", process.pid), events)
            events.append(("wait", process.pid))
            return real_wait(process, *args, **kwargs)

        with mock.patch.object(process_runner.os, "killpg", side_effect=killpg), \
                mock.patch.object(subprocess.Popen, "wait", wait), \
                mock.patch.object(subprocess.Popen, "poll", side_effect=AssertionError("must not reap with poll")), \
                mock.patch.object(subprocess.Popen, "communicate", side_effect=AssertionError("must not use communicate")):
            result = self.run_code("import os,time\npid=os.fork()\nif pid==0:\n time.sleep(5)\n os._exit(0)\nraise SystemExit(4)")
        self.assert_clean(result, 4)
        self.assertEqual(result.group_cleanup, "signaled_owned_group")
        self.assertTrue(result.direct_child_reaped)
        self.assertEqual([event[0] for event in events], ["signal", "wait"])

    def test_completed_child_and_eof_need_no_zombie_group_signal(self):
        with mock.patch.object(process_runner.os, "killpg", side_effect=AssertionError("no live pipe to clean up")):
            result = self.run_code("print('complete')")
        self.assert_clean(result)
        self.assertEqual(result.stdout, b"complete\n")
        self.assertEqual(result.group_cleanup, "not_attempted_normal_exit")
        self.assertTrue(result.direct_child_reaped)

    def test_signal_failure_is_not_cleanup_success(self):
        with mock.patch.object(process_runner.os, "killpg", side_effect=PermissionError(errno.EPERM, "denied")):
            result = self.run_code("import time; time.sleep(0.1)", timeout=0.04)
        self.assertTrue(result.timed_out)
        self.assertEqual(result.returncode, 0)
        self.assertIn("process-group cleanup failed", result.cleanup_error)
        self.assertEqual(result.group_cleanup, "uncertain")
        self.assertTrue(result.direct_child_reaped)

    def test_receipt_fields_have_backwards_compatible_defaults(self):
        result = process_runner.ProcessResult(0, b"", b"", False, False, None, 0.0)
        self.assertEqual(result.group_cleanup, "not_attempted")
        self.assertFalse(result.direct_child_reaped)

    def test_unsupported_waitid_never_spawns(self):
        with mock.patch.object(process_runner.os, "waitid", None), \
                mock.patch.object(subprocess, "Popen", side_effect=AssertionError("must not spawn")):
            result = self.run_code("pass")
        self.assertIsNone(result.returncode)
        self.assertIn("unsupported", result.cleanup_error)

    def test_waitid_api_refusal_is_infrastructure(self):
        with mock.patch.object(process_runner.os, "waitid", side_effect=OSError(errno.ENOSYS, "not supported")), \
                mock.patch.object(subprocess, "Popen", side_effect=AssertionError("must not spawn")):
            result = self.run_code("pass")
        self.assertIsNone(result.returncode)
        self.assertIn("unsupported waitid", result.cleanup_error)

    def test_foreign_sigchld_handler_is_explicitly_unsupported(self):
        with mock.patch.object(process_runner.signal, "getsignal", return_value=signal.SIG_IGN), \
                mock.patch.object(subprocess, "Popen", side_effect=AssertionError("must not spawn")):
            result = self.run_code("pass")
        self.assertIsNone(result.returncode)
        self.assertIn("SIGCHLD", result.cleanup_error)

    def test_invalid_limits_do_not_spawn(self):
        for limits in ({"timeout": 0}, {"timeout": float("inf")}, {"timeout": float("nan")},
                       {"cleanup_seconds": -1}, {"output_limit": -1}, {"output_limit": True}):
            with mock.patch.object(subprocess, "Popen", side_effect=AssertionError("must not spawn")):
                result = self.run_code("pass", **limits)
            self.assertIsNone(result.returncode)
            self.assertIn("invalid process", result.cleanup_error)


if __name__ == "__main__":
    unittest.main()
