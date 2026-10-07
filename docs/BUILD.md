# Build the local candidate

Supported bootstrap: macOS arm64 on Lean 4.35.0-rc4 and Rust 1.96.0. The same
Lean source also builds on the latest stable 4.34.1 in a scratch compatibility
lane. Neither observation qualifies a release or the untrusted submission gate.
The source GitHub workflow proposes Linux x86_64 checks; its hosted run remains
unperformed until the operator creates/publishes the repository.

Install the official pinned Lean archive explicitly into caller-owned scratch;
verify its SHA-256 from toolchains/lean.json before extraction. The core has no
Lake dependency downloads. Directly select that archive's bin directory instead
of substituting a host elan default. Rust dependencies are resolved by Cargo.lock.

From the project root, select directories outside the source checkout:

```sh
# Setup is explicit; this fetch prepares an offline registry cache.
CARGO_HOME="$VJ_CARGO_HOME" cargo fetch --locked
python3 -B tools/check.py --lean-bin "$VJ_LEAN_BIN" \
  --cargo-home "$VJ_CARGO_HOME" --work "$VJ_CHECK_WORK"
```

The check destination must not already exist. The driver copies Lean source into
that fresh directory, builds native artifacts, audits each named proof root's
axioms, replays the imported closure with Lean's kernel, runs synthetic oracle
observations and verifier metadata tests, and builds/tests locked offline Rust.
No setup hook, download, publication or reporter runs during the check. Evidence
contains PASS_BOOTSTRAP_CHECKS or NONPASS_BOOTSTRAP_CHECKS and always records
proof_gate=NOT_QUALIFIED. A source build is not community mathematical admission.
Independent replay has a separate trusted-maintainer adapter. On the measured
Darwin arm64 RC distribution, after the fresh build, run:

```sh
python3 -B tools/verification/bootstrap_replay.py \
  --toolchain "$VJ_LEAN_TOOLCHAIN_ROOT" \
  --module-root "$VJ_CHECK_WORK/lean/.lake/build/lib/lean" \
  --roots proofs/roots.json --work "$VJ_REPLAY_WORK" \
  --manifest tools/verification/rc4-bootstrap-tools.json \
  --expected-manifest-sha256 49bbd746f22088ffbfc7180b875d39be7fae53196f67ba312fd956d44224c173 \
  --trusted-bootstrap
```

The explicit acknowledgment applies only to your known trusted build. The adapter
reports completed/not-established observations and cannot open a community
packet. The manifest binds the measured Mac binaries; Linux identities and the
full adversarial supervisor need separate qualification. See
[verifier limits](../tools/verification/README.md) for the broader String-literal
export gap and independent-checker diagnostics.

For metadata tests only:

```sh
python3 -B tools/check.py --python-only --work "$VJ_METADATA_WORK"
```

The full driver writes native oracle and CLI paths into result.json. The CLI
compares original immutable JSON bytes with serde_json's documented exact-token,
sequence-preserving scalar-string profile:

```sh
"$VJ_DIFF" --oracle "$VJ_ORACLE" --input sample.json
"$VJ_DIFF" --oracle "$VJ_ORACLE" --hex 6e756c6c
printf '%s\n' '6e756c6c' | "$VJ_ORACLE"
```

Oracle output is a VJ1 envelope carrying a binary AST as hex. --serialize is an
experimental oracle mode returning VJ1<TAB>json<TAB>ASCII_JSON_HEX, used by
round-trip observation tests; the comparison CLI uses the default AST mode.
Do not feed private production data to public issues or synthetic test corpora.

## Toolchain updates and promotion

Development uses an exact RC pin, never a moving latest selector. Maintainers
prepare newer RC proposals with official commit/archive hashes, repeat build,
axiom and replay checks, compare frozen meanings and then refresh affected
packets. The source sets fixedToolchain=true and warnings are fatal.

Stable qualification uses a separate fresh source copy and stable compiler pin;
it does not rewrite an existing RC artifact. Stable promotion additionally needs
the complete source/runtime/codec qualification and reviewed package identities.
The current stable compatibility build is evidence of compatibility only.
Publication remains a later explicit operator action. GitHub's native Actions
workflow UI can run qualification; no custom claim service is introduced.
