#!/usr/bin/env python3
# Copyright 2026 Verified JSON contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded packet/source inspection. This bootstrap never admits a Lean proof."""

from __future__ import annotations

import argparse
import errno
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
from typing import Any

MAX_PACKET_BYTES = 128 * 1024
# Bound decimal conversion independently of any looser interpreter setting.
# A stricter Python conversion limit remains in force and is caught below.
MAX_JSON_INTEGER_DIGITS = 4096
MAX_SUBMISSION_BYTES = 8 * 1024 * 1024
MAX_SUBMISSION_ENTRIES = 512
MAX_PATH_DEPTH = 32
CLASSES = {
    "proof-only", "implementation-with-proofs", "tests-docs",
    "maintainer-contract-release-infrastructure",
}
MATHEMATICAL_CLASSES = {"proof-only", "implementation-with-proofs"}
UNIMPLEMENTED_STAGES = (
    "authenticated_qualified_envelope", "isolated_elaboration_and_teardown",
    "frozen_declaration_comparison", "transitive_axiom_audit",
    "official_kernel_replay", "independent_kernel_replay", "integration_rebuild",
)


class GuardError(Exception):
    def __init__(self, code: str, message: str, *, infra: bool = False):
        super().__init__(message)
        self.code, self.infra = code, infra


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise GuardError("DUPLICATE_JSON_KEY", f"Duplicate key: {key}")
        out[key] = value
    return out


def _integer(text: str) -> int:
    if len(text) - int(text.startswith("-")) > MAX_JSON_INTEGER_DIGITS:
        raise GuardError("INVALID_JSON", "JSON integer exceeds the preflight digit bound")
    return int(text)


def _relative_path(value: Any, *, scope: bool = False) -> str:
    if not isinstance(value, str) or not value or len(value) > 512:
        raise GuardError("INVALID_PATH", "Paths must be nonempty bounded strings")
    if "\\" in value or ":" in value or any(ord(c) < 32 for c in value):
        raise GuardError("INVALID_PATH", "Nonportable or control-character path")
    base = value.removesuffix("/**") if scope else value
    base = base.removesuffix("/") if scope else base
    parts = base.split("/")
    if len(parts) > MAX_PATH_DEPTH or any(x in {"", ".", ".."} for x in parts):
        raise GuardError("INVALID_PATH", "Absolute, traversing or noncanonical path")
    if PurePosixPath(base).is_absolute() or any(x in base for x in "*?[]"):
        raise GuardError("INVALID_PATH", "Only explicit paths, directories and final /** scopes are allowed")
    if not scope and value != base:
        raise GuardError("INVALID_PATH", "Artifact paths must name exact files")
    return value


def _paths(value: Any, name: str) -> list[str]:
    if not isinstance(value, list) or len(value) > MAX_SUBMISSION_ENTRIES:
        raise GuardError("INVALID_SCOPE", f"{name} must be a bounded list")
    values = [_relative_path(v, scope=True) for v in value]
    if len(set(values)) != len(values):
        raise GuardError("INVALID_SCOPE", f"Duplicate {name} entries")
    return values


def _allows(scope: str, path: str) -> bool:
    if scope.endswith("/**"):
        return path.startswith(scope[:-3] + "/")
    if scope.endswith("/"):
        return path.startswith(scope)
    return path == scope


def _overlaps(a: str, b: str) -> bool:
    abase, bbase = a.removesuffix("/**").rstrip("/"), b.removesuffix("/**").rstrip("/")
    return abase == bbase or _allows(a, bbase) or _allows(b, abase)


def _read_regular(path: Path, limit: int) -> bytes:
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            raise GuardError("SYMLINK_INPUT", "Input file cannot be a symlink") from exc
        raise GuardError("UNREADABLE_INPUT", str(exc), infra=True) from exc
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise GuardError("SPECIAL_INPUT", "Input must be a regular file")
        with os.fdopen(fd, "rb", closefd=False) as stream:
            data = stream.read(limit + 1)
        if len(data) > limit:
            raise GuardError("INPUT_LIMIT", "Input exceeds the declared preflight limit")
        return data
    finally:
        os.close(fd)


def _submission_files(root: Path, allowed: list[str], readonly: list[str]) -> dict[str, str]:
    """Walk opened directory descriptors; do not follow candidate symlinks."""
    hashes: dict[str, str] = {}
    entries, total = 0, 0
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    try:
        root_fd = os.open(root, flags | os.O_DIRECTORY)
    except OSError as exc:
        if root.is_symlink():
            raise GuardError("SYMLINK_INPUT", "Submission root cannot be a symlink") from exc
        raise GuardError("UNREADABLE_SUBMISSION", str(exc), infra=True) from exc

    def walk(dir_fd: int, prefix: str, depth: int) -> None:
        nonlocal entries, total
        if depth > MAX_PATH_DEPTH:
            raise GuardError("TREE_LIMIT", "Submission directory depth exceeds policy")
        with os.scandir(dir_fd) as iterator:
            children = []
            for child in iterator:
                entries += 1
                if entries > MAX_SUBMISSION_ENTRIES:
                    raise GuardError("TREE_LIMIT", "Too many submission entries")
                children.append(child)
            children.sort(key=lambda e: e.name)
        for child in children:
            rel = prefix + child.name
            _relative_path(rel)
            if child.is_symlink():
                raise GuardError("SYMLINK_INPUT", f"Symlink in submission: {rel}")
            try:
                child_fd = os.open(child.name, flags, dir_fd=dir_fd)
            except OSError as exc:
                if exc.errno == errno.ELOOP:
                    raise GuardError("SYMLINK_INPUT", f"Changed symlink in submission: {rel}") from exc
                raise GuardError("UNREADABLE_SUBMISSION", str(exc), infra=True) from exc
            try:
                mode = os.fstat(child_fd).st_mode
                if stat.S_ISDIR(mode):
                    walk(child_fd, rel + "/", depth + 1)
                elif stat.S_ISREG(mode):
                    if not any(_allows(x, rel) for x in allowed) or any(_allows(x, rel) for x in readonly):
                        raise GuardError("UNAUTHORIZED_FILE", f"File outside permitted scope: {rel}")
                    with os.fdopen(child_fd, "rb", closefd=False) as stream:
                        data = stream.read(MAX_SUBMISSION_BYTES - total + 1)
                    total += len(data)
                    if total > MAX_SUBMISSION_BYTES:
                        raise GuardError("TREE_LIMIT", "Submission bytes exceed policy")
                    hashes[rel] = hashlib.sha256(data).hexdigest()
                else:
                    raise GuardError("SPECIAL_INPUT", f"Nonregular submission entry: {rel}")
            finally:
                os.close(child_fd)

    try:
        walk(root_fd, "", 0)
    finally:
        os.close(root_fd)
    return hashes


def inspect_packet(packet_path: str | Path, submission_root: str | Path | None = None,
                   *, expected_packet_sha256: str | None = None) -> dict[str, Any]:
    """Inspect data only. No argv, candidate code or receipt is executed/trusted."""
    result: dict[str, Any] = {
        "schema_version": 1, "scope": "packet-preflight", "verdict": "INFRA",
        "candidate_executed": False, "full_acceptance_available": False,
        "stages": [], "packet_sha256": None, "submission_files": {},
    }

    def checked(name: str) -> None:
        result["stages"].append({"name": name, "performed": True, "result": "accepted-data"})

    try:
        raw = _read_regular(Path(packet_path), MAX_PACKET_BYTES)
        digest = hashlib.sha256(raw).hexdigest()
        result["packet_sha256"] = digest
        if expected_packet_sha256 is not None:
            if not isinstance(expected_packet_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_packet_sha256):
                raise GuardError("INVALID_EXPECTED_DIGEST", "Expected packet identity must be SHA-256")
            if digest != expected_packet_sha256:
                raise GuardError("PACKET_IDENTITY_MISMATCH", "Packet bytes differ from caller's expected identity")
        checked("packet_bytes")
        packet = json.loads(raw, object_pairs_hook=_object, parse_int=_integer,
                            parse_constant=lambda _: (_ for _ in ()).throw(GuardError("INVALID_JSON", "Nonfinite JSON constant")))
        if not isinstance(packet, dict) or not re.fullmatch(r"VJ-\d{3}", str(packet.get("id", ""))):
            raise GuardError("INVALID_PACKET", "Expected a packet object with a VJ-NNN ID")
        if not isinstance(packet.get("ticket_class"), str) or packet["ticket_class"] not in CLASSES or type(packet.get("claim_ready")) is not bool:
            raise GuardError("INVALID_PACKET", "Unknown class or nonboolean readiness flag")
        allowed = _paths(packet.get("allowed_files"), "allowed_files")
        readonly = _paths(packet.get("read_only_contract_paths", []), "read_only_contract_paths")
        outputs = _paths(packet.get("output_artifacts"), "output_artifacts")
        if not allowed or outputs != allowed or any(_overlaps(a, b) for a in allowed for b in readonly):
            raise GuardError("INVALID_SCOPE", "Empty/conflicting scope or mismatched declared outputs")
        checked("packet_scope")
        if submission_root is not None:
            hashes = _submission_files(Path(submission_root), allowed, readonly)
            result["submission_files"] = hashes
            claimed = packet.get("submission_manifest")
            if claimed is not None:
                if not isinstance(claimed, dict) or claimed != hashes:
                    raise GuardError("SUBMISSION_MANIFEST_MISMATCH", "Claimed manifest differs from scoped source bytes")
            checked("submission_scope_and_bytes")
        elif packet.get("submission_manifest") is not None:
            raise GuardError("SUBMISSION_UNAVAILABLE", "Cannot inspect a manifest without source", infra=True)
        validator = packet.get("validator")
        if not isinstance(validator, dict):
            raise GuardError("INVALID_VALIDATOR", "Missing validator descriptor")
        if not packet["claim_ready"]:
            result.update(code="NOT_READY", message="Template is not activated; no candidate execution is permitted")
        elif packet["ticket_class"] not in MATHEMATICAL_CLASSES:
            result.update(code="MANUAL_REVIEW_REQUIRED", message="This class uses a frozen human review policy, not automatic proof admission")
        else:
            if not isinstance(packet.get("status"), str) or packet["status"] in {"candidate-unfrozen", "draft", "blocked"}:
                raise GuardError("READINESS_CONTRADICTION", "Ready mathematical packet still has an unfrozen/blocked status")
            for field in ("frozen_target_pin", "packet_revision", "packet_digest", "contract_pin", "toolchain_closure_pin"):
                if packet.get(field) in (None, "", [], {}):
                    raise GuardError("READINESS_CONTRADICTION", f"Ready mathematical packet lacks {field}")
            for field in ("declaration_bindings", "meaning_bearing_definition_bindings", "input_output_bindings"):
                if not isinstance(packet.get(field), list) or not packet[field]:
                    raise GuardError("READINESS_CONTRADICTION", f"Ready mathematical packet lacks {field}")
            argv = validator.get("argv")
            if validator.get("status") != "READY" or validator.get("identity") in (None, ""):
                raise GuardError("READINESS_CONTRADICTION", "Validator is not bound and ready")
            if not isinstance(argv, list) or not argv or any(not isinstance(x, str) or not x or "\0" in x for x in argv):
                raise GuardError("INVALID_VALIDATOR", "Validator argv must be a nonempty argument vector")
            result.update(code="FULL_GATE_UNIMPLEMENTED", message="Claims of readiness do not authenticate a qualified envelope; full gate is unavailable")
        checked("readiness_inspection")
    except GuardError as exc:
        result.update(verdict="INFRA" if exc.infra else "REJECT", code=exc.code, message=str(exc))
    except (UnicodeError, ValueError, RecursionError) as exc:
        result.update(verdict="REJECT", code="INVALID_JSON", message=type(exc).__name__)
    except OSError as exc:
        result.update(verdict="INFRA", code="INPUT_IO_FAILURE", message=str(exc))
    result["stages"].extend({"name": x, "performed": False, "result": "UNIMPLEMENTED"} for x in UNIMPLEMENTED_STAGES)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--submission", type=Path)
    parser.add_argument("--expected-sha256")
    args = parser.parse_args()
    result = inspect_packet(args.packet, args.submission, expected_packet_sha256=args.expected_sha256)
    print(json.dumps(result, sort_keys=True))
    return 2 if result["verdict"] == "REJECT" else 3


if __name__ == "__main__":
    raise SystemExit(main())
