# Copyright 2026 Verified JSON contributors
# SPDX-License-Identifier: Apache-2.0
"""Source identity for trusted bootstrap checks; not an authenticated proof gate."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import stat

AXIOMS = frozenset({'propext', 'Quot.sound', 'Classical.choice'})
ROOT_FILES = ('proofs/roots.json', 'proofs/document-spec-roots.json')
SKIP_DIRS = frozenset({'.git', '.lake', 'target', '__pycache__'})
NAME = re.compile(r'[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+')
HEX = re.compile(r'[0-9a-f]{64}')


def digest_file(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f'expected regular source file: {path}')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_files(root: Path) -> dict[str, str]:
    """Exact regular-file bytes used by the developer snapshot; exclude build caches."""
    files = {}
    def walk(directory: Path):
        for p in sorted(directory.iterdir()):
            if p.name in SKIP_DIRS and p.is_dir():
                continue
            mode = p.lstat().st_mode
            if stat.S_ISLNK(mode):
                raise ValueError(f'symlink source is unsupported: {p.relative_to(root)}')
            if stat.S_ISDIR(mode):
                walk(p)
            elif stat.S_ISREG(mode):
                files[p.relative_to(root).as_posix()] = digest_file(p)
            else:
                raise ValueError(f'special source file is unsupported: {p.relative_to(root)}')
    walk(root)
    return files


def files_digest(files: dict[str, str]) -> str:
    raw = json.dumps(files, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def snapshot_source(root: Path, dest: Path) -> dict[str, str]:
    """Copy once and confirm bytes; subsequent build/test commands use only this copy."""
    original = source_files(root)
    dest.mkdir(parents=True, exist_ok=False)
    for name in original:
        target = dest / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / name, target)
    copied = source_files(dest)
    if copied != original or source_files(root) != original:
        raise ValueError('source changed while snapshotting; retry from a stable checkout')
    return copied


def _binding(root: Path, value: object) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != {'path', 'sha256'}:
        raise ValueError('source binding requires exact path/sha256 fields')
    path, expected = value['path'], value['sha256']
    if not isinstance(path, str) or not path or '\\' in path:
        raise ValueError('invalid source binding path')
    parts = path.split('/')
    if any(p in ('', '.', '..') for p in parts) or PurePosixPath(path).is_absolute():
        raise ValueError('source binding path must be canonical and relative')
    if not isinstance(expected, str) or not HEX.fullmatch(expected):
        raise ValueError('source binding requires SHA-256')
    target = root.joinpath(*parts)
    current = root
    for part in parts:
        current = current / part
        if current.is_symlink():
            raise ValueError('symlink source binding')
    actual = digest_file(target)
    if actual != expected:
        raise ValueError(f'stale source binding: {path}')
    return {'path': path, 'sha256': actual}


def load_root_manifest(root: Path, relative: str) -> dict:
    path = root / relative
    raw = path.read_bytes()  # Required, not optional.
    record = json.loads(raw)
    if not isinstance(record, dict):
        raise ValueError('root manifest must be an object')
    declarations = record.get('declarations')
    if not isinstance(declarations, list) or not declarations or any(
            not isinstance(n, str) or not NAME.fullmatch(n) for n in declarations):
        raise ValueError('nonempty qualified root declarations required')
    if len(set(declarations)) != len(declarations):
        raise ValueError('duplicate root declaration')
    axioms = record.get('allowed_axioms')
    if not isinstance(axioms, list) or any(not isinstance(a, str) for a in axioms) or set(axioms) != AXIOMS or len(axioms) != len(AXIOMS):
        raise ValueError('root manifest changed the fixed bootstrap axiom basis')
    meanings = record.get('meaning_roots', [])
    if not isinstance(meanings, list) or len(meanings) > 128 or any(
            not isinstance(n, str) or not NAME.fullmatch(n) for n in meanings):
        raise ValueError('invalid meaning-bearing root declarations')
    if len(set(meanings)) != len(meanings):
        raise ValueError('duplicate meaning-bearing root')
    bindings = record.get('source_bindings')
    if not isinstance(bindings, list) or not bindings:
        raise ValueError('source bindings required')
    checked = [_binding(root, b) for b in bindings]
    if len({b['path'] for b in checked}) != len(checked):
        raise ValueError('duplicate source binding')
    if relative == 'proofs/document-spec-roots.json':
        required = {'lean/VerifiedJson/DocumentSpec.lean', 'lean/VerifiedJson/Spec.lean', 'lean/VerifiedJson/Grammar.lean'}
        if {b['path'] for b in checked} != required:
            raise ValueError('contract must bind exact DocumentSpec/Spec/Grammar sources')
        source = next(b['sha256'] for b in checked if b['path'].endswith('/DocumentSpec.lean'))
        if record.get('source_sha256') != source:
            raise ValueError('contract source_sha256 differs from its source binding')
    return {**record, 'manifest_path': relative, 'manifest_sha256': hashlib.sha256(raw).hexdigest(),
            'source_bindings': checked}


def load_root_set(root: Path) -> list[dict]:
    records = [load_root_manifest(root, rel) for rel in ROOT_FILES]
    names = [n for record in records for n in record['declarations']]
    if len(set(names)) != len(names):
        raise ValueError('duplicate proof root across manifests')
    return records
