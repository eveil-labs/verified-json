# Copyright 2026 Verified JSON contributors
# SPDX-License-Identifier: Apache-2.0
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "verification"))
from preflight import inspect_packet


class PacketPreflightTests(unittest.TestCase):
    def setUp(self):
        work = os.environ.get("VERIFIED_JSON_TEST_WORK")
        if not work or not Path(work).is_dir():
            raise RuntimeError("Set VERIFIED_JSON_TEST_WORK to an allocated existing test scratch directory")
        self.tmp = tempfile.TemporaryDirectory(dir=work)
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.packet = json.loads((REPO / "work-packets" / "VJ-009.json").read_text())
        self.path = self.root / "packet.json"

    def inspect(self, submission=None):
        self.path.write_text(json.dumps(self.packet))
        return inspect_packet(self.path, submission)

    def assertNoExecution(self, result):
        self.assertFalse(result["candidate_executed"])
        self.assertFalse(result["full_acceptance_available"])
        self.assertNotEqual(result["verdict"], "PASS")
        self.assertTrue(all(not s["performed"] for s in result["stages"] if s["result"] == "UNIMPLEMENTED"))

    def test_every_current_template_is_infra_not_a_proof_verdict(self):
        for path in sorted((REPO / "work-packets").glob("VJ-*.json")):
            result = inspect_packet(path)
            self.assertEqual((result["verdict"], result["code"]), ("INFRA", "NOT_READY"), path)
            self.assertNoExecution(result)

    def test_flip_ready_flag_cannot_activate_template(self):
        self.packet["claim_ready"] = True
        result = self.inspect()
        self.assertEqual(result["code"], "READINESS_CONTRADICTION")
        self.assertEqual(result["verdict"], "REJECT")
        self.assertNoExecution(result)

    def test_forged_qualified_packet_and_executable_argv_still_do_not_run(self):
        self.packet.update(status="sealed", claim_ready=True)
        for field in ("frozen_target_pin", "packet_revision", "packet_digest", "contract_pin", "toolchain_closure_pin"):
            self.packet[field] = "1" * 64
        for field in ("declaration_bindings", "meaning_bearing_definition_bindings", "input_output_bindings"):
            self.packet[field] = ["forged"]
        marker = self.root / "EXECUTED"
        self.packet["validator"] = {"status": "READY", "identity": "forged", "argv": [sys.executable, "-c", f"open({str(marker)!r}, 'w').write('bad')"]}
        self.packet["receipt"] = {"verdict": "PASS", "qualified": True}
        result = self.inspect()
        self.assertEqual((result["verdict"], result["code"]), ("INFRA", "FULL_GATE_UNIMPLEMENTED"))
        self.assertFalse(marker.exists())
        self.assertNoExecution(result)

    def test_manual_ready_class_does_not_need_fake_lean_receipt(self):
        self.packet.update(ticket_class="tests-docs", status="sealed", claim_ready=True)
        result = self.inspect()
        self.assertEqual((result["verdict"], result["code"]), ("INFRA", "MANUAL_REVIEW_REQUIRED"))

    def test_invalid_scope_paths_are_rejected_before_any_execution(self):
        for path in ("../outside", "/absolute", "a/../b", "./a", "a//b", "C:/windows", "a\\b", "**", "a/*.lean", "a/\x00b"):
            self.packet["allowed_files"] = self.packet["output_artifacts"] = [path]
            result = self.inspect()
            self.assertEqual(result["verdict"], "REJECT", path)
            self.assertNoExecution(result)

    def test_conflicting_output_and_readonly_scopes_are_rejected(self):
        self.packet["read_only_contract_paths"] = ["lean/VerifiedJson/Impl/"]
        self.assertEqual(self.inspect()["code"], "INVALID_SCOPE")
        self.packet["read_only_contract_paths"] = []
        self.packet["output_artifacts"] = ["other.lean"]
        self.assertEqual(self.inspect()["code"], "INVALID_SCOPE")

    def test_duplicate_json_keys_are_not_last_write_wins(self):
        self.path.write_text('{"id":"VJ-009","id":"VJ-010"}')
        result = inspect_packet(self.path)
        self.assertEqual(result["code"], "DUPLICATE_JSON_KEY")

    def test_malformed_structural_types_fail_closed(self):
        original = dict(self.packet)
        for key, value in (("ticket_class", {}), ("claim_ready", 1), ("validator", []), ("allowed_files", "file.lean")):
            self.packet = dict(original)
            self.packet[key] = value
            result = self.inspect()
            self.assertEqual(result["verdict"], "REJECT", key)
            self.assertNoExecution(result)

    def test_packet_external_identity_mismatch_rejects(self):
        self.path.write_text(json.dumps(self.packet))
        self.assertEqual(inspect_packet(self.path, expected_packet_sha256="0" * 64)["code"], "PACKET_IDENTITY_MISMATCH")
        digest = hashlib.sha256(self.path.read_bytes()).hexdigest()
        self.assertEqual(inspect_packet(self.path, expected_packet_sha256=digest)["code"], "NOT_READY")

    def test_packet_symlink_and_submission_symlink_reject(self):
        self.path.write_text(json.dumps(self.packet))
        link = self.root / "linked-packet.json"
        link.symlink_to(self.path)
        self.assertEqual(inspect_packet(link)["code"], "SYMLINK_INPUT")
        submission = self.root / "source"
        submission.mkdir()
        (submission / "escape").symlink_to(self.root)
        self.assertEqual(inspect_packet(self.path, submission)["code"], "SYMLINK_INPUT")

    def test_scoped_owned_file_manifest_and_forgery(self):
        submission = self.root / "source"
        leaf = submission / "lean/VerifiedJson/Impl/Cursor.lean"
        leaf.parent.mkdir(parents=True)
        leaf.write_text("-- generic nonexecuted fixture\n")
        rel = "lean/VerifiedJson/Impl/Cursor.lean"
        self.packet["submission_manifest"] = {rel: hashlib.sha256(leaf.read_bytes()).hexdigest()}
        result = self.inspect(submission)
        self.assertEqual(result["code"], "NOT_READY")
        self.packet["submission_manifest"][rel] = "0" * 64
        self.assertEqual(self.inspect(submission)["code"], "SUBMISSION_MANIFEST_MISMATCH")
        self.assertNoExecution(result)

    def test_out_of_scope_file_is_rejected(self):
        submission = self.root / "source"
        submission.mkdir()
        (submission / "policy.py").write_text("raise RuntimeError('must not execute')")
        self.assertEqual(self.inspect(submission)["code"], "UNAUTHORIZED_FILE")

    def test_missing_packet_is_infrastructure(self):
        result = inspect_packet(self.root / "missing.json")
        self.assertEqual(result["verdict"], "INFRA")
        self.assertNoExecution(result)


if __name__ == "__main__":
    unittest.main()
