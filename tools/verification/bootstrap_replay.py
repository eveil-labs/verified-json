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
from typing import Any

from preflight import GuardError, _object, _read_regular
from process_runner import run_bounded
from source_envelope import source_files, files_digest, load_root_manifest

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
           "VerifiedJson.String", "VerifiedJson.Serializer", "VerifiedJson.DocumentSpec",
           "VerifiedJson.Transport", "VerifiedJson.Parser"]
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
                     trusted_bootstrap: bool = False, source_root: Path | None = None,
                     expected_source_sha256: str | None = None,
                     expected_roots_sha256: str | None = None) -> dict[str, Any]:
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
        if expected_roots_sha256 is None or hashlib.sha256(raw_roots).hexdigest() != expected_roots_sha256:
            raise GuardError("ROOTS_IDENTITY_MISMATCH", "Caller must bind the exact root-manifest bytes", infra=True)
        if source_root is None or expected_source_sha256 is None:
            raise GuardError("SOURCE_BINDING_REQUIRED", "Trusted source snapshot identity is required", infra=True)
        source_map = source_files(source_root)
        if files_digest(source_map) != expected_source_sha256:
            raise GuardError("SOURCE_IDENTITY_MISMATCH", "Source snapshot differs from caller's pin")
        try:
            relative_roots = roots_path.resolve().relative_to(source_root.resolve()).as_posix()
        except ValueError as exc:
            raise GuardError("ROOTS_OUTSIDE_SOURCE", "Root manifest must belong to the bound source snapshot") from exc
        roots_record = load_root_manifest(source_root, relative_roots)
        roots = roots_record.get("declarations") if isinstance(roots_record, dict) else None
        if not isinstance(roots, list) or not roots or len(roots) > 128 or any(not isinstance(n, str) or not NAME.fullmatch(n) for n in roots):
            raise GuardError("INVALID_ROOTS", "Nonempty bounded declaration names required")
        axioms = roots_record.get("allowed_axioms")
        if len(set(roots)) != len(roots) or not isinstance(axioms, list) or any(not isinstance(a, str) for a in axioms) or sorted(axioms) != sorted(AXIOMS):
            raise GuardError("INVALID_ROOTS", "Duplicate roots or widened axiom policy")
        meanings = roots_record.get("meaning_roots", [])
        roots = list(dict.fromkeys(roots + meanings))
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
                      roots_sha256=hashlib.sha256(raw_roots).hexdigest(), roots=roots,
                      source_files_map_sha256=expected_source_sha256,
                      source_bindings=roots_record["source_bindings"],
                      source_artifact_correspondence="bound source identity and observed objects; caller supplies fresh trusted build",
                      olean_sha256={module: hashlib.sha256(module_root.joinpath(*module.split(".")).with_suffix(".olean").read_bytes()).hexdigest() for module in MODULES})

        def stage(name: str, argv: list[str], *, stdout_file: Path | None = None) -> tuple[int, str]:
            proc = run_bounded(argv, env=env, cwd=module_root, timeout=60)
            code, stdout, stderr = proc.returncode, proc.stdout, proc.stderr
            if proc.timed_out or proc.output_limited or proc.cleanup_error or proc.returncode is None or not proc.direct_child_reaped:
                code = 124
            result["stages"].append({"name": name + "_lifecycle", "performed": True,
                "timed_out": proc.timed_out, "output_limited": proc.output_limited,
                "cleanup_error": proc.cleanup_error, "group_cleanup": proc.group_cleanup,
                "direct_child_reaped": proc.direct_child_reaped})
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
        if source_files(source_root) != source_map:
            raise GuardError("SOURCE_CHANGED", "Source snapshot changed during replay")
        result["status"] = "completed" if native == independent == 0 else "not-established"
        result["reason"] = "Observed exact engine exits on caller-trusted built source; not a qualified community gate"
    except (GuardError, OSError, UnicodeError, ValueError, RecursionError) as exc:
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
    p.add_argument("--source-root", type=Path, required=True)
    p.add_argument("--expected-source-sha256", required=True)
    p.add_argument("--expected-roots-sha256", required=True)
    args = p.parse_args()
    result = replay_bootstrap(toolchain=args.toolchain.resolve(), module_root=args.module_root,
        roots_path=args.roots, work=args.work, manifest_path=args.manifest,
        expected_manifest_sha256=args.expected_manifest_sha256, trusted_bootstrap=args.trusted_bootstrap,
        source_root=args.source_root, expected_source_sha256=args.expected_source_sha256,
        expected_roots_sha256=args.expected_roots_sha256)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "completed" else 3


if __name__ == "__main__":
    raise SystemExit(main())
