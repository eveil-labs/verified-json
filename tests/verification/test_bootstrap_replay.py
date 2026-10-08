# Copyright 2026 Verified JSON contributors
# SPDX-License-Identifier: Apache-2.0
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools/verification"))
from bootstrap_replay import MODULES, TOOLS, replay_bootstrap, validate_manifest
from preflight import GuardError
from process_runner import ProcessResult
from source_envelope import files_digest, snapshot_source


class TrustedBootstrapBoundaryTests(unittest.TestCase):
    def setUp(self):
        work = os.environ.get("VERIFIED_JSON_TEST_WORK")
        if not work or not Path(work).is_dir():
            raise RuntimeError("Allocate VERIFIED_JSON_TEST_WORK first")
        self.tmp = tempfile.TemporaryDirectory(dir=work)
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.manifest = self.root / "manifest.json"

    def test_no_bootstrap_acknowledgment_never_starts_process(self):
        with patch("bootstrap_replay.run_bounded") as run:
            result = replay_bootstrap(toolchain=self.root, module_root=self.root, roots_path=self.root,
                work=self.root, manifest_path=self.root, expected_manifest_sha256="0" * 64)
        run.assert_not_called()
        self.assertFalse(result["community_acceptance_available"])
        self.assertEqual(result["status"], "not-established")

    def test_tool_manifest_forgery_never_starts_process(self):
        self.manifest.write_text('{}')
        with patch("bootstrap_replay.run_bounded") as run:
            result = replay_bootstrap(toolchain=self.root, module_root=self.root, roots_path=self.root,
                work=self.root, manifest_path=self.manifest, expected_manifest_sha256="0" * 64,
                trusted_bootstrap=True)
        run.assert_not_called()
        self.assertEqual(result["code"], "MANIFEST_IDENTITY_MISMATCH")

    def test_missing_fixed_role_binary_is_not_qualification(self):
        value = {"lean_githash": "1" * 40, "binaries": {x: "0" * 64 for x in ("lean", "leanexport", "leanchecker-paranoid", "nanoda_bin")}}
        self.manifest.write_text(json.dumps(value))
        digest = hashlib.sha256(self.manifest.read_bytes()).hexdigest()
        with self.assertRaises(GuardError) as ctx:
            validate_manifest(self.manifest, digest, self.root)
        self.assertEqual(ctx.exception.code, "MISSING_TOOL")

    def test_compiler_hash_must_be_a_string_not_a_coerced_integer(self):
        self.manifest.write_text(json.dumps({"lean_githash": int("1" * 40), "binaries": {}}))
        digest = hashlib.sha256(self.manifest.read_bytes()).hexdigest()
        with self.assertRaises(GuardError) as ctx:
            validate_manifest(self.manifest, digest, self.root)
        self.assertEqual(ctx.exception.code, "INVALID_TOOL_MANIFEST")

    def bound_inputs(self):
        source = self.root / "source"
        pin = files_digest(snapshot_source(REPO, source))
        binaries = self.root / "bin"
        binaries.mkdir()
        hashes = {}
        for name in TOOLS:
            binary = binaries / name
            binary.write_bytes(name.encode())
            hashes[name] = hashlib.sha256(binary.read_bytes()).hexdigest()
        self.manifest.write_text(json.dumps({"lean_githash": "1" * 40, "binaries": hashes}))
        modules = self.root / "modules"
        for name in MODULES:
            artifact = modules.joinpath(*name.split(".")).with_suffix(".olean")
            artifact.parent.mkdir(parents=True, exist_ok=True)
            artifact.write_bytes(name.encode())
        roots = source / "proofs/document-spec-roots.json"
        return dict(toolchain=self.root, module_root=modules, roots_path=roots,
                    work=self.root / "evidence", manifest_path=self.manifest,
                    expected_manifest_sha256=hashlib.sha256(self.manifest.read_bytes()).hexdigest(),
                    trusted_bootstrap=True, source_root=source, expected_source_sha256=pin,
                    expected_roots_sha256=hashlib.sha256(roots.read_bytes()).hexdigest())

    def test_changed_source_or_manifest_pin_never_starts_process(self):
        args = self.bound_inputs()
        for field, code in (("expected_source_sha256", "SOURCE_IDENTITY_MISMATCH"),
                            ("expected_roots_sha256", "ROOTS_IDENTITY_MISMATCH")):
            with self.subTest(field=field), patch("bootstrap_replay.run_bounded") as run:
                result = replay_bootstrap(**{**args, field: "0" * 64})
                self.assertEqual(result["code"], code)
                run.assert_not_called()

    def test_stale_semantic_dependency_binding_never_starts_process(self):
        args = self.bound_inputs()
        grammar = args["source_root"] / "lean/VerifiedJson/Grammar.lean"
        grammar.write_bytes(grammar.read_bytes() + b"\n-- changed dependency\n")
        from source_envelope import source_files
        args["expected_source_sha256"] = files_digest(source_files(args["source_root"]))
        with patch("bootstrap_replay.run_bounded") as run:
            result = replay_bootstrap(**args)
        run.assert_not_called()
        self.assertEqual(result["status"], "not-established")
        self.assertIn("stale source binding", result["reason"])

    def test_missing_document_module_never_starts_process(self):
        args = self.bound_inputs()
        (args["module_root"] / "VerifiedJson/DocumentSpec.olean").unlink()
        with patch("bootstrap_replay.run_bounded") as run:
            result = replay_bootstrap(**args)
        run.assert_not_called()
        self.assertEqual(result["code"], "MISSING_MODULE")

    @staticmethod
    def completed(stdout=b"checked\n"):
        return ProcessResult(0, stdout, b"", False, False, None, 0.01,
                             "not_attempted_normal_exit", True)

    def test_export_includes_top_level_contract_meanings(self):
        args = self.bound_inputs()
        with patch("bootstrap_replay.run_bounded", side_effect=[
                self.completed(b"Lean commit " + b"1" * 40), self.completed(b"export\xff"),
                self.completed(), self.completed()]) as run:
            result = replay_bootstrap(**args)
        self.assertEqual(result["status"], "completed")
        export_argv = run.call_args_list[1].args[0]
        for name in ("VerifiedJson.DocumentSpec", "VerifiedJson.DocumentSpec.Document",
                     "VerifiedJson.DocumentSpec.FitsLimits", "VerifiedJson.DocumentSpec.Utf8Text"):
            self.assertIn(name, export_argv)
        self.assertFalse(result["community_acceptance_available"])
        raw = (args["work"] / "export.stdout").read_bytes()
        self.assertEqual(raw, b"export\xff")
        stage = next(s for s in result["stages"] if s["name"] == "export")
        self.assertEqual(stage["stdout_sha256"], hashlib.sha256(raw).hexdigest())

    def test_zero_exit_without_owned_reap_is_not_completion(self):
        args = self.bound_inputs()
        unowned = ProcessResult(0, b"Lean commit " + b"1" * 40, b"", False, False,
                                None, 0.01, "uncertain", False)
        with patch("bootstrap_replay.run_bounded", return_value=unowned) as run:
            result = replay_bootstrap(**args)
        self.assertEqual(result["status"], "not-established")
        self.assertEqual(result["code"], "COMPILER_IDENTITY")
        self.assertEqual(run.call_count, 1)

    def test_independent_failure_retains_native_success_but_is_not_completion(self):
        args = self.bound_inputs()
        failed = ProcessResult(1, b"", b"rejected", False, False, None, 0.01,
                               "not_attempted_normal_exit", True)
        with patch("bootstrap_replay.run_bounded", side_effect=[
                self.completed(b"Lean commit " + b"1" * 40), self.completed(b"export"),
                self.completed(), failed]):
            result = replay_bootstrap(**args)
        self.assertEqual(result["status"], "not-established")
        self.assertEqual(next(s for s in result["stages"] if s["name"] == "official_replay")["exit_code"], 0)
        self.assertEqual(next(s for s in result["stages"] if s["name"] == "independent_replay")["exit_code"], 1)


if __name__ == "__main__":
    unittest.main()
