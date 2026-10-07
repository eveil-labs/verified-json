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
from bootstrap_replay import replay_bootstrap, validate_manifest
from preflight import GuardError


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
        with patch("bootstrap_replay.subprocess.run") as run:
            result = replay_bootstrap(toolchain=self.root, module_root=self.root, roots_path=self.root,
                work=self.root, manifest_path=self.root, expected_manifest_sha256="0" * 64)
        run.assert_not_called()
        self.assertFalse(result["community_acceptance_available"])
        self.assertEqual(result["status"], "not-established")

    def test_tool_manifest_forgery_never_starts_process(self):
        self.manifest.write_text('{}')
        with patch("bootstrap_replay.subprocess.run") as run:
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


if __name__ == "__main__":
    unittest.main()
