#!/usr/bin/env python3
# Copyright 2026 Verified JSON contributors
# SPDX-License-Identifier: Apache-2.0
"""Replay an explicitly trusted maintainer build; never admit community input."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Any

from preflight import GuardError, _object, _read_regular

TOOLS = ("lean", "leanexport", "leanchecker-paranoid", "nanoda_bin")
AXIOMS = ["propext", "Quot.sound", "Classical.choice"]
# Public upstream primitive list, plus quotient primitives. Apache-2.0 origin:
# leanprover/comparator ca04cfc72b550331658ec314bf47685281bfd4bf/Main.lean.
PRIMITIVES = [
    "Nat.add", "Nat.sub", "Nat.mul", "Nat.pow", "Nat.gcd", "Nat.div", "Nat.mod",
    "Nat.beq", "Nat.ble", "Nat.land", "Nat.lor", "Nat.xor", "Nat.shiftLeft",
    "Nat.shiftRight", "String.ofList", "Char.ofNat", "List", "eagerReduce",
    "Nat", "String", "String.mk", "Char", "optParam", "autoParam", "semiOutParam",
    "outParam", "Quot", "Quot.mk", "Quot.lift", "Quot.ind",
]
MODULES = ["VerifiedJson.Cursor", "VerifiedJson.Grammar", "VerifiedJson.Number",
           "VerifiedJson.String", "VerifiedJson.Serializer"]
NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+")


def validate_manifest(path: Path, expected_sha256: str, toolchain: Path) -> dict[str, Any]:
    raw = _read_regular(path, 128 * 1024)
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise GuardError("MANIFEST_IDENTITY_MISMATCH", "Tool manifest differs from independently supplied identity")
    manifest = json.loads(raw, object_pairs_hook=_object)
    if not isinstance(manifest, dict) or not isinstance(manifest.get("lean_githash"), str) or not re.fullmatch(r"[0-9a-f]{40}", manifest["lean_githash"]):
        raise GuardError("INVALID_TOOL_MANIFEST", "Exact Lean source identity required")
    bindings = manifest.get("binaries")
    if not isinstance(bindings, dict) or set(bindings) != set(TOOLS):
        raise GuardError("INVALID_TOOL_MANIFEST", "All fixed-role binaries must be hash-bound")
    for name in TOOLS:
        expected = bindings[name]
        if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
            raise GuardError("INVALID_TOOL_MANIFEST", "Binary identities must be SHA-256")
        binary = toolchain / "bin" / name
        if binary.is_symlink() or not binary.is_file():
            raise GuardError("MISSING_TOOL", f"Unavailable regular binary: {name}", infra=True)
        if hashlib.sha256(_read_regular(binary, 256 * 1024 * 1024)).hexdigest() != expected:
            raise GuardError("TOOL_IDENTITY_MISMATCH", f"Changed binary: {name}")
    return manifest


def replay_bootstrap(*, toolchain: Path, module_root: Path, roots_path: Path,
                     work: Path, manifest_path: Path, expected_manifest_sha256: str,
                     trusted_bootstrap: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {"schema_version": 1, "scope": "trusted-maintainer-bootstrap",
        "status": "not-established", "community_acceptance_available": False,
        "source_artifact_correspondence": "caller must supply a fresh trusted build",
        "stages": []}
    if not trusted_bootstrap:
        result["reason"] = "Explicit trusted-bootstrap acknowledgment required; never use on adversarial submissions"
        return result
    try:
        manifest = validate_manifest(manifest_path, expected_manifest_sha256, toolchain)
        raw_roots = _read_regular(roots_path, 128 * 1024)
        roots_record = json.loads(raw_roots, object_pairs_hook=_object)
        roots = roots_record.get("declarations") if isinstance(roots_record, dict) else None
        if not isinstance(roots, list) or not roots or len(roots) > 128 or any(not isinstance(n, str) or not NAME.fullmatch(n) for n in roots):
            raise GuardError("INVALID_ROOTS", "Nonempty bounded declaration names required")
        axioms = roots_record.get("allowed_axioms")
        if len(set(roots)) != len(roots) or not isinstance(axioms, list) or any(not isinstance(a, str) for a in axioms) or sorted(axioms) != sorted(AXIOMS):
            raise GuardError("INVALID_ROOTS", "Duplicate roots or widened axiom policy")
        if module_root.is_symlink() or not module_root.is_dir():
            raise GuardError("MISSING_MODULE_ROOT", "Trusted compiled module root unavailable", infra=True)
        for module in MODULES:
            artifact = module_root.joinpath(*module.split(".")).with_suffix(".olean")
            if artifact.is_symlink() or not artifact.is_file():
                raise GuardError("MISSING_MODULE", f"No trusted built artifact for {module}", infra=True)
        if work.exists():
            raise GuardError("WORK_EXISTS", "Use a fresh allocated work directory; prior evidence is preserved", infra=True)
        work.mkdir(parents=True)
        env = {"PATH": str(toolchain / "bin") + ":/usr/bin:/bin", "LEAN_PATH": str(module_root),
               "TMPDIR": str(work), "LEAN_ABORT_ON_PANIC": "1"}
        result.update(tool_manifest_sha256=expected_manifest_sha256,
                      roots_sha256=hashlib.sha256(raw_roots).hexdigest(), roots=roots)

        def stage(name: str, argv: list[str], *, stdout_file: Path | None = None) -> tuple[int, str]:
            try:
                proc = subprocess.run(argv, env=env, cwd=module_root, stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE, timeout=60)
                code, stdout, stderr = proc.returncode, proc.stdout, proc.stderr
            except subprocess.TimeoutExpired:
                code, stdout, stderr = 124, b"", b"Timeout: process result not established"
            (work / (name + ".stdout")).write_bytes(stdout)
            (work / (name + ".stderr")).write_bytes(stderr)
            if stdout_file is not None:
                stdout_file.write_bytes(stdout)
            result["stages"].append({"name": name, "performed": True, "exit_code": code,
                "stdout_sha256": hashlib.sha256(stdout).hexdigest(),
                "stderr_sha256": hashlib.sha256(stderr).hexdigest()})
            return code, stdout.decode("utf-8", errors="replace")

        code, version = stage("compiler_identity", [str(toolchain / "bin/lean"), "--version"])
        if code or manifest["lean_githash"] not in version:
            raise GuardError("COMPILER_IDENTITY", "Effective Lean does not match manifest", infra=True)
        export = work / "closure.jsonl"
        code, _ = stage("export", [str(toolchain / "bin/leanexport"), *MODULES, "--", *roots, *PRIMITIVES], stdout_file=export)
        if code or export.stat().st_size == 0:
            raise GuardError("EXPORT_UNAVAILABLE", "Selected closure export not established", infra=True)
        result["export_sha256"] = hashlib.sha256(export.read_bytes()).hexdigest()
        config = work / "nanoda.json"
        config.write_text(json.dumps({"export_file_path": str(export), "use_stdin": False,
            "permitted_axioms": AXIOMS, "unpermitted_axiom_hard_error": True,
            "nat_extension": True, "string_extension": True, "num_threads": 1,
            "print_success_message": True, "pp_declars": []}) + "\n")
        native, _ = stage("official_replay", [str(toolchain / "bin/leanchecker-paranoid"), "--from-export", str(export)])
        independent, _ = stage("independent_replay", [str(toolchain / "bin/nanoda_bin"), str(config)])
        result["status"] = "completed" if native == independent == 0 else "not-established"
        result["reason"] = "Observed exact engine exits on caller-trusted built source; not a qualified community gate"
    except (GuardError, OSError, UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        result["reason"] = str(exc)
        result["code"] = exc.code if isinstance(exc, GuardError) else "INFRASTRUCTURE_FAILURE"
    return result


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--toolchain", type=Path, required=True)
    p.add_argument("--module-root", type=Path, required=True)
    p.add_argument("--roots", type=Path, required=True)
    p.add_argument("--work", type=Path, required=True)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--expected-manifest-sha256", required=True)
    p.add_argument("--trusted-bootstrap", action="store_true")
    args = p.parse_args()
    result = replay_bootstrap(toolchain=args.toolchain.resolve(), module_root=args.module_root,
        roots_path=args.roots, work=args.work, manifest_path=args.manifest,
        expected_manifest_sha256=args.expected_manifest_sha256, trusted_bootstrap=args.trusted_bootstrap)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "completed" else 3


if __name__ == "__main__":
    raise SystemExit(main())
