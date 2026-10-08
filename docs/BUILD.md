# Build the local candidate

Supported bootstrap: macOS arm64 on Lean 4.35.0-rc4 and Rust 1.96.0. The same
Lean source also builds on the latest stable 4.34.1 in a scratch compatibility
lane. Neither observation qualifies a release or the untrusted submission gate.
The hosted GitHub Linux x86_64 bootstrap build/test workflow also passed after
the operator published the repository. This remains candidate behavior evidence.

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
The driver copies the entire regular-file source tree to a verified fresh snapshot,
then requires both proof-root manifests and checks their source bindings in that copy.
Lean and Cargo checks use that snapshot. result.json records its file-map digest,
Spec/Grammar/DocumentSpec bindings, root manifest hashes, compiler/Rust/feature
identities, all native artifact hashes and per-stage lifecycle/log observations.
`--expected-source-sha256` can bind an independently supplied source-files-map
pin. This is checked identity evidence for a trusted invocation; it does not
authenticate an adversarial contributor or establish compiled refinement.

Each stage bounds time, output and cleanup. Normal exited+EOF completion reaps the
owned direct child without signaling its group; no absence of silent descendants
is established. When stopping an unfinished, timed-out or output-limited observation,
the runner signals while the
leader is unreaped, closes pipes after the bounded drain, and records uncertainty.
The caller must exclusively own reaping; SIGCHLD auto-reaping/another reaper is
unsupported. This remains a trusted bootstrap lifecycle boundary, not a sandbox.

Independent replay uses the exact measured Darwin arm64 tools. The source snapshot
and root-manifest hashes are read from the completed build receipt; they are not
recomputed from an arbitrary changed checkout. Use the manifest_path and
manifest_sha256 for the root set you want from result.json:

```sh
python3 -B tools/verification/bootstrap_replay.py \
  --toolchain "$VJ_LEAN_TOOLCHAIN_ROOT" \
  --module-root "$VJ_CHECK_WORK/lean/.lake/build/lib/lean" \
  --source-root "$VJ_CHECK_WORK/source" \
  --expected-source-sha256 "$VJ_RECORDED_SOURCE_PIN" \
  --roots "$VJ_CHECK_WORK/source/proofs/document-spec-roots.json" \
  --expected-roots-sha256 "$VJ_RECORDED_CONTRACT_ROOT_PIN" \
  --work "$VJ_REPLAY_WORK" \
  --manifest tools/verification/rc4-bootstrap-tools.json \
  --expected-manifest-sha256 49bbd746f22088ffbfc7180b875d39be7fae53196f67ba312fd956d44224c173 \
  --trusted-bootstrap
```

This contract recipe imports DocumentSpec and exports its witnesses plus explicit
meaning roots, including Document/FitsLimits/Utf8Text. Use a separate fresh replay
work directory and the implementation roots.json binding for the helper/implementation
set. The adapter records source/root/tool/object/export hashes and does not create
community PASS. It still assumes a fresh trusted source/build relationship; objects
and dynamic tool dependencies are not adversarially sealed. The Linux kernel
identities, broader String export gap and qualified worker remain separate work.
See [verifier limits](../tools/verification/README.md).

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
