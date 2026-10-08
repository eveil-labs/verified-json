# Copyright 2026 Verified JSON contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded observation of trusted bootstrap subprocesses, not a sandbox.

The caller must be the sole waiter for the child (no concurrent waitpid(-1)
reaper). WNOWAIT keeps its PID reserved until any group signalling has finished.
An exited child with both pipes at EOF needs no group signal; this does not prove
absence of silent descendants. Escaped descendants are not contained: inherited
pipes are closed after bounded cleanup and reported as infrastructure failure,
without signalling other groups.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import os
from pathlib import Path
import selectors
import signal
import subprocess
import time
from typing import Mapping, Sequence


@dataclass(frozen=True)
class ProcessResult:
    returncode: int | None
    stdout: bytes
    stderr: bytes
    timed_out: bool
    output_limited: bool
    cleanup_error: str | None
    duration_seconds: float
    group_cleanup: str = "not_attempted"
    direct_child_reaped: bool = False


def _waitid_support_error() -> str | None:
    required = ("waitid", "WNOWAIT", "WEXITED", "WNOHANG", "P_PID", "killpg")
    if os.name != "posix" or any(getattr(os, name, None) is None for name in required):
        return "unsupported platform: waitid(WNOWAIT) and process groups are required"
    if signal.getsignal(signal.SIGCHLD) != signal.SIG_DFL:
        return "unsupported SIGCHLD handler: exclusive child-wait ownership is required"
    try:
        # Our own PID cannot be our child. ECHILD confirms that this API and
        # option combination is callable without creating or reaping anything.
        os.waitid(os.P_PID, os.getpid(), os.WEXITED | os.WNOHANG | os.WNOWAIT)
    except ChildProcessError:
        return None
    except (OSError, NotImplementedError) as exc:
        return f"unsupported waitid(WNOWAIT): {exc}"
    return "unsupported waitid(WNOWAIT): unexpected self-wait result"


def run_bounded(argv: Sequence[str], *, cwd: str | Path, env: Mapping[str, str],
                timeout: float, output_limit: int = 32 * 1024 * 1024,
                cleanup_seconds: float = 0.25, merge_stderr: bool = False) -> ProcessResult:
    """Capture a bounded byte prefix, with a deadline covering pipes and child.

    The output limit is shared by stdout and stderr. No wait for pipe EOF can
    extend execution beyond timeout plus cleanup_seconds. Native process-spawn
    and OS system-call responsiveness remain host assumptions. A timeout, output
    cap, absent returncode or cleanup_error is an infrastructure outcome; even a
    zero returncode does not override those fields. Never use this as proof of
    adversarial descendant containment.
    """
    started = time.monotonic()
    stdout, stderr = bytearray(), bytearray()
    timed_out, output_limited = False, False
    errors: list[str] = []
    returncode: int | None = None
    group_cleanup = "not_attempted"
    direct_child_reaped = False

    def result() -> ProcessResult:
        return ProcessResult(returncode, bytes(stdout), bytes(stderr), timed_out,
                             output_limited, "; ".join(errors) or None,
                             time.monotonic() - started, group_cleanup,
                             direct_child_reaped)

    try:
        valid_limits = (isinstance(timeout, (int, float)) and not isinstance(timeout, bool)
                        and math.isfinite(timeout) and timeout > 0
                        and isinstance(cleanup_seconds, (int, float)) and not isinstance(cleanup_seconds, bool)
                        and math.isfinite(cleanup_seconds) and cleanup_seconds >= 0
                        and type(output_limit) is int and output_limit >= 0)
    except (TypeError, ValueError, OverflowError):
        valid_limits = False
    if not valid_limits:
        errors.append("invalid process observation limits")
        return result()
    unsupported = _waitid_support_error()
    if unsupported:
        errors.append(unsupported)
        return result()
    try:
        process = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT if merge_stderr else subprocess.PIPE,
                                   bufsize=0, close_fds=True, start_new_session=True)
    except (OSError, ValueError, TypeError) as exc:
        errors.append(f"spawn failed: {exc}")
        return result()

    selector: selectors.BaseSelector | None = None
    streams = [stream for stream in (process.stdout, process.stderr) if stream is not None]
    owns_child = True
    observed_exit = False
    deadline = started + timeout

    def read_ready(events: list[tuple[selectors.SelectorKey, int]]) -> None:
        nonlocal output_limited
        assert selector is not None
        for key, _ in events:
            remaining = output_limit - len(stdout) - len(stderr)
            try:
                chunk = os.read(key.fd, min(65536, remaining + 1))
            except BlockingIOError:
                continue
            if not chunk:
                selector.unregister(key.fileobj)
                key.fileobj.close()
                continue
            target = stdout if key.data == "stdout" else stderr
            target.extend(chunk[:remaining])
            if len(chunk) > remaining:
                output_limited = True
                return

    try:
        selector = selectors.DefaultSelector()
        for stream in streams:
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ,
                              "stdout" if stream is process.stdout else "stderr")
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                timed_out = True
                break
            try:
                observed = os.waitid(os.P_PID, process.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
            except ChildProcessError:
                # A different waiter or host policy already reaped the child.
                # Its numeric PID/PGID is no longer a safe signal capability.
                owns_child = False
                group_cleanup = "uncertain"
                errors.append("child wait ownership lost; process group was not signalled")
                break
            if observed is not None and observed.si_pid == process.pid:
                observed_exit = True
                # Drain only bytes already available; EOF is evidence about
                # these pipes, not about all descendants. A Darwin group with
                # only an unreaped zombie returns EPERM from killpg, so a
                # completed child with complete output needs no group signal.
                while selector.get_map() and not output_limited:
                    if time.monotonic() >= deadline:
                        timed_out = True
                        break
                    ready = selector.select(0)
                    if not ready:
                        break
                    read_ready(ready)
                break
            read_ready(selector.select(min(0.02, remaining)))
            if output_limited:
                break
    except (OSError, ValueError, NotImplementedError) as exc:
        errors.append(f"process observation failed: {exc}")
    finally:
        cleanup_deadline = time.monotonic() + cleanup_seconds
        needs_cleanup = (not observed_exit or timed_out or output_limited
                         or selector is None or bool(selector.get_map()))
        if owns_child and needs_cleanup:
            try:
                # No poll(), communicate(), or reaping wait has run. In
                # particular, even an exited leader still reserves this PID.
                os.killpg(process.pid, signal.SIGKILL)
                group_cleanup = "signaled_owned_group"
            except ProcessLookupError:
                group_cleanup = "group_absent"
            except OSError as exc:
                group_cleanup = "uncertain"
                errors.append(f"process-group cleanup failed: {exc}")
        elif owns_child and not needs_cleanup:
            group_cleanup = "not_attempted_normal_exit"
        try:
            # This is the first reaping operation. No group signal follows it.
            observed_returncode = process.wait(timeout=max(0.0, cleanup_deadline - time.monotonic()))
            if owns_child:
                returncode = observed_returncode
                direct_child_reaped = True
        except (subprocess.TimeoutExpired, OSError) as exc:
            errors.append(f"child reaping not established within cleanup bound: {exc}")
        try:
            while selector is not None and selector.get_map() and not output_limited:
                remaining = cleanup_deadline - time.monotonic()
                if remaining <= 0:
                    errors.append("output pipe EOF not established within cleanup bound; pipes closed")
                    break
                read_ready(selector.select(min(0.01, remaining)))
        except (OSError, ValueError) as exc:
            errors.append(f"output cleanup failed: {exc}")
        finally:
            for stream in streams:
                stream.close()
            if selector is not None:
                selector.close()
    return result()
