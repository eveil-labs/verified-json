#!/usr/bin/env python3
"""Source-bound trusted-developer bootstrap checks; not an untrusted proof gate.

Setup/fetch is explicit. Generated snapshots, Lean/Cargo artifacts and evidence
live only in a newly allocated --work directory outside the checkout.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/verification'))
from process_runner import run_bounded
from source_envelope import AXIOMS, files_digest, load_root_set, snapshot_source, source_files


def run(argv, *, cwd, env, work, name, timeout=240):
    result = run_bounded(argv, cwd=cwd, env=env, timeout=timeout, merge_stderr=True)
    output = result.stdout.decode('utf-8', errors='replace')
    (work / f'{name}.log').write_bytes(result.stdout)
    observation = {'name': name, 'argv': argv, 'exit': result.returncode,
                   'duration_seconds': result.duration_seconds, 'timed_out': result.timed_out,
                   'output_limited': result.output_limited, 'cleanup_error': result.cleanup_error,
                   'group_cleanup': result.group_cleanup,
                   'direct_child_reaped': result.direct_child_reaped,
                   'log_sha256': hashlib.sha256(result.stdout).hexdigest()}
    (work / f'{name}.json').write_text(json.dumps(observation, indent=2) + '\n')
    if result.timed_out or result.output_limited or result.cleanup_error or result.returncode is None or not result.direct_child_reaped:
        raise RuntimeError(f'{name}: infrastructure result {observation}')
    if result.returncode:
        print(output[-12000:], file=sys.stderr)
        raise RuntimeError(f'{name}: exit {result.returncode}')
    return observation


def audit_axioms(text: str, roots: list[str]) -> dict[str, list[str]]:
    observed = {}
    for line in text.splitlines():
        match = re.fullmatch(r"'([^']+)' depends on axioms: \[(.*)\]", line)
        empty = re.fullmatch(r"'([^']+)' does not depend on any axioms", line)
        if match or empty:
            name = (match or empty)[1]
            if name in observed:
                raise RuntimeError('duplicate axiom-root binding')
            observed[name] = [x.strip() for x in match[2].split(',') if x.strip()] if match else []
    if set(observed) != set(roots):
        raise RuntimeError('axiom audit did not bind every exact requested root')
    if any(set(axioms) - AXIOMS for axioms in observed.values()):
        raise RuntimeError('root depends on an unapproved axiom')
    return observed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--python-only', action='store_true')
    parser.add_argument('--lean-bin', type=Path, help='exact installed RC bin directory')
    parser.add_argument('--work', type=Path, required=True, help='new generated-output directory')
    parser.add_argument('--cargo-home', type=Path, help='explicit pre-fetched offline Cargo home')
    parser.add_argument('--expected-source-sha256', help='optional independently supplied source-files-map pin')
    args = parser.parse_args()
    work = args.work.resolve()
    if work.exists() or work == ROOT or ROOT in work.parents:
        parser.error('--work must be fresh and outside the checkout')
    if not args.python_only and args.lean_bin is None:
        parser.error('full checks require --lean-bin; setup is explicit')
    work.mkdir(parents=True)
    checks = []
    record = {'scope': 'trusted-developer-bootstrap', 'proof_gate': 'NOT_QUALIFIED',
              'community_packets': 'NOT_READY', 'contract_semantic_approval': 'PENDING',
              'checks': checks, 'source_correspondence': 'copied bytes checked; not authenticated adversarial sealing'}
    try:
        source = work / 'source'
        files = snapshot_source(ROOT, source)
        pin = files_digest(files)
        if args.expected_source_sha256 is not None and args.expected_source_sha256 != pin:
            raise RuntimeError('source snapshot differs from caller-supplied pin')
        record['source'] = {'recipe': 'SHA256 compact sorted JSON relative-file-path -> regular-file SHA256 map',
                            'files_map_sha256': pin, 'files': files}
        records = load_root_set(source)  # Both manifest files and source bindings are required.
        record['root_manifests'] = records
        env = os.environ.copy()
        env['PYTHONDONTWRITEBYTECODE'] = '1'
        test_work = work / 'test-scratch'; test_work.mkdir()
        env['VERIFIED_JSON_TEST_WORK'] = str(test_work)
        if args.python_only:
            checks.append(run([sys.executable, '-B', '-m', 'unittest', 'discover', '-s',
                               'tests/verification', '-v'], cwd=source, env=env, work=work,
                              name='python-metadata-tests'))
        else:
            bin_dir = args.lean_bin.resolve()
            lock = json.loads((source / 'toolchains/lean.json').read_text())['development']
            env['PATH'] = str(bin_dir) + os.pathsep + env.get('PATH', '')
            checks.append(run([str(bin_dir / 'lean'), '--version'], cwd=source, env=env,
                              work=work, name='compiler-identity', timeout=15))
            version = (work / 'compiler-identity.log').read_text()
            if lock['version'].removeprefix('v') not in version or lock['commit'] not in version:
                raise RuntimeError('effective compiler differs from the development pin')
            record['compiler'] = {'version': version.strip(), 'commit': lock['commit'],
                                  'binary_sha256': hashlib.sha256((bin_dir / 'lean').read_bytes()).hexdigest()}
            lean = work / 'lean'
            shutil.copytree(source / 'lean', lean)
            checks.append(run([str(bin_dir / 'lake'), 'build'], cwd=lean, env=env,
                              work=work, name='lean-build'))
            oracle = lean / '.lake/build/bin/verified-json-oracle'
            obj = lean / '.lake/build/lib/lean/VerifiedJson.olean'
            regression = lean / '.lake/build/bin/verified-json-api-regression'
            if not all(p.is_file() for p in [oracle, obj, regression]):
                raise RuntimeError('successful build lacks required fresh artifacts')
            checks.append(run([str(regression)], cwd=lean, env=env, work=work,
                              name='lean-api-regressions', timeout=30))
            roots = [name for manifest in records for name in manifest['declarations']]
            meanings = [name for manifest in records for name in manifest.get('meaning_roots', [])]
            audit_roots = list(dict.fromkeys(roots + meanings))
            record['root_scopes'] = {'implementation_helpers': len(records[0]['declarations']),
                                     'draft_contract_witnesses': len(records[1]['declarations']),
                                     'meaning_definitions': len(set(meanings))}
            audit = lean / 'BootstrapAudit.lean'
            audit.write_text('import VerifiedJson\n' + '\n'.join(f'#print axioms {n}' for n in audit_roots) + '\n')
            checks.append(run([str(bin_dir / 'lake'), 'env', 'lean', str(audit)],
                              cwd=lean, env=env, work=work, name='axiom-audit'))
            record['axioms'] = audit_axioms((work / 'axiom-audit.log').read_text(), audit_roots)
            checks.append(run([str(bin_dir / 'lake'), 'env', str(bin_dir / 'leanchecker'),
                               '--fresh', 'VerifiedJson'], cwd=lean, env=env, work=work,
                              name='same-kernel-replay'))
            env['VJ_ORACLE'] = str(oracle)
            checks.append(run([sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-v'],
                              cwd=source, env=env, work=work, name='python-tests'))
            env['CARGO_TARGET_DIR'] = str(work / 'cargo-target')
            if args.cargo_home:
                env['CARGO_HOME'] = str(args.cargo_home.resolve())
            for name, argv in [('rust-identity', ['rustc', '--version']), ('cargo-identity', ['cargo', '--version']),
                               ('cargo-features', ['cargo', 'tree', '--workspace', '--locked', '--offline', '-e', 'features']),
                               ('cargo-metadata', ['cargo', 'metadata', '--locked', '--offline', '--format-version', '1']),
                               ('rust-tests', ['cargo', 'test', '--workspace', '--locked', '--offline']),
                               ('rust-build', ['cargo', 'build', '--workspace', '--locked', '--offline'])]:
                checks.append(run(argv, cwd=source, env=env, work=work, name=name))
            diff = work / 'cargo-target/debug/verified-json-diff'
            if not diff.is_file():
                raise RuntimeError('Rust build did not produce its CLI')
            record['artifacts'] = {name: {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
                                   for name, path in [('oracle', oracle), ('root_olean', obj), ('rust_cli', diff)]}
            record['rust'] = {'compiler': (work / 'rust-identity.log').read_text().strip(),
                              'cargo': (work / 'cargo-identity.log').read_text().strip(),
                              'feature_tree_sha256': hashlib.sha256((work / 'cargo-features.log').read_bytes()).hexdigest(),
                              'cargo_lock_sha256': files['Cargo.lock']}
        if source_files(source) != files:
            raise RuntimeError('snapshotted source changed during checks; no source-bound success')
        record['status'] = 'PASS_BOOTSTRAP_CHECKS'
    except (OSError, RuntimeError, ValueError) as error:
        record['status'] = 'NONPASS_BOOTSTRAP_CHECKS'
        record['error'] = str(error)
    (work / 'result.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record, indent=2))
    return 0 if record['status'] == 'PASS_BOOTSTRAP_CHECKS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
