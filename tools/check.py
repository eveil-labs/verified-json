#!/usr/bin/env python3
"""Fresh trusted-developer bootstrap checks. Not an untrusted submission gate.

Never downloads dependencies or changes toolchains. All generated Lean/Cargo
artifacts go to a newly allocated --work directory outside the source tree.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]

def run(argv, *, cwd, env, work, name, timeout=240):
    start = time.time()
    proc = subprocess.Popen(argv, cwd=cwd, env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, start_new_session=True)
    try:
        output, _ = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        output, _ = proc.communicate()
        (work / f"{name}.log").write_text(output)
        raise RuntimeError(f"{name}: infrastructure timeout")
    (work / f"{name}.log").write_text(output)
    result = {"name": name, "argv": argv, "exit": proc.returncode,
              "started_at": start, "duration_seconds": time.time() - start}
    if proc.returncode:
        print(output[-12000:], file=sys.stderr)
        raise RuntimeError(f"{name}: exit {proc.returncode}")
    return result

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--python-only", action="store_true",
                   help="run metadata/verifier unit tests only, no Lean/Rust claim")
    p.add_argument("--lean-bin", type=Path, help="exact installed RC bin directory")
    p.add_argument("--work", type=Path, help="new, nonexistent generated-output directory")
    p.add_argument("--cargo-home", type=Path, help="pre-fetched offline Cargo registry directory")
    a = p.parse_args()
    if a.python_only:
        if not a.work:
            p.error("--python-only also requires a fresh --work for tests")
        test_work = a.work.resolve()
        if test_work.exists() or test_work == ROOT or ROOT in test_work.parents:
            p.error("--work must be a fresh directory outside the source project")
        test_work.mkdir(parents=True)
        test_env = os.environ.copy()
        test_env["VERIFIED_JSON_TEST_WORK"] = str(test_work)
        test_env["PYTHONDONTWRITEBYTECODE"] = "1"
        return subprocess.call([sys.executable, "-B", "-m", "unittest", "discover",
                                "-s", "tests/verification", "-v"], cwd=ROOT, env=test_env)
    if a.lean_bin is None or a.work is None:
        p.error("full checks require --lean-bin and --work; dependency setup is explicit")
    work = a.work.resolve()
    if work == ROOT or ROOT in work.parents:
        p.error("generated work must be outside the source project")
    if work.exists():
        p.error("--work already exists: retain it and choose a fresh destination")
    work.mkdir(parents=True)
    results = []
    record = {"scope": "trusted-developer-bootstrap", "proof_gate": "NOT_QUALIFIED",
              "community_packets": "NOT_READY", "checks": results}
    try:
        bin_dir = a.lean_bin.resolve()
        lock = json.loads((ROOT / "toolchains/lean.json").read_text())["development"]
        actual = subprocess.check_output([str(bin_dir / "lean"), "--version"], text=True)
        if lock["version"].removeprefix("v") not in actual or lock["commit"] not in actual:
            raise RuntimeError("Lean version/commit differs from the exact development pin")
        env = os.environ.copy()
        env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        test_work = work / "verification-tests"
        test_work.mkdir()
        env["VERIFIED_JSON_TEST_WORK"] = str(test_work)
        lean = work / "lean"
        shutil.copytree(ROOT / "lean", lean, ignore=shutil.ignore_patterns(".lake"))
        results.append(run([str(bin_dir / "lake"), "build"], cwd=lean, env=env,
                           work=work, name="lean-build"))
        oracle = lean / ".lake/build/bin/verified-json-oracle"
        root_artifact = lean / ".lake/build/lib/lean/VerifiedJson.olean"
        if not oracle.is_file() or not root_artifact.is_file():
            raise RuntimeError("successful build did not produce required fresh artifacts")
        roots_path = ROOT / "proofs/roots.json"
        if roots_path.is_file():
            roots = json.loads(roots_path.read_text())["declarations"]
            if not roots:
                raise RuntimeError("empty proof-root audit is not meaningful evidence")
            audit = lean / "BootstrapAudit.lean"
            audit.write_text("import VerifiedJson\n" + "\n".join(
                f"#print axioms {name}" for name in roots) + "\n")
            results.append(run([str(bin_dir / "lake"), "env", "lean", str(audit)],
                               cwd=lean, env=env, work=work, name="axiom-audit"))
            printed = (work / "axiom-audit.log").read_text()
            observed = {}
            for line in printed.splitlines():
                m = re.fullmatch(r"'([^']+)' depends on axioms: \[(.*)\]", line)
                empty = re.fullmatch(r"'([^']+)' does not depend on any axioms", line)
                if empty:
                    if empty[1] in observed: raise RuntimeError("duplicate axiom-root binding")
                    observed[empty[1]] = []
                if m:
                    if m[1] in observed: raise RuntimeError("duplicate axiom-root binding")
                    observed[m[1]] = [x.strip() for x in m[2].split(",") if x.strip()]
            if set(observed) != set(roots):
                raise RuntimeError("axiom audit did not bind every exact requested proof root")
            allowed = set(json.loads(roots_path.read_text())["allowed_axioms"])
            if any(set(axioms) - allowed for axioms in observed.values()):
                raise RuntimeError("proof root depends on an unapproved axiom")
            record["axioms"] = observed
        results.append(run([str(bin_dir / "lake"), "env", str(bin_dir / "leanchecker"),
                            "--fresh", "VerifiedJson"], cwd=lean, env=env, work=work,
                           name="same-kernel-replay"))
        env["VJ_ORACLE"] = str(oracle)
        results.append(run([sys.executable, "-B", "-m", "unittest", "discover",
                            "-s", "tests", "-v"], cwd=ROOT, env=env, work=work,
                           name="python-tests"))
        env["CARGO_TARGET_DIR"] = str(work / "cargo-target")
        if a.cargo_home:
            env["CARGO_HOME"] = str(a.cargo_home.resolve())
        results.append(run(["cargo", "test", "--workspace", "--locked", "--offline"],
                           cwd=ROOT, env=env, work=work, name="rust-tests"))
        results.append(run(["cargo", "build", "--workspace", "--locked", "--offline"],
                           cwd=ROOT, env=env, work=work, name="rust-build"))
        diff = work / "cargo-target/debug/verified-json-diff"
        record["artifacts"] = {"oracle": {"path": str(oracle), "sha256": hashlib.sha256(
            oracle.read_bytes()).hexdigest()}, "root_olean": hashlib.sha256(
            root_artifact.read_bytes()).hexdigest(), "rust_cli": str(diff)}
        record["status"] = "PASS_BOOTSTRAP_CHECKS"
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
        record["status"] = "NONPASS_BOOTSTRAP_CHECKS"
        record["error"] = str(error)
    (work / "result.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2))
    return 0 if record["status"] == "PASS_BOOTSTRAP_CHECKS" else 1

if __name__ == "__main__":
    raise SystemExit(main())
