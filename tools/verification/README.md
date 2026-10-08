# Verifier bootstrap

The packet preflight is implemented; the mathematical acceptance supervisor is
not. `preflight.py` reads bounded JSON metadata and optionally inspects scoped
source files without following candidate symlinks. It never runs `validator.argv`,
imports a candidate module, executes Lean, trusts an uploaded PASS receipt, or
produces mathematical PASS.

Its Python interface is `inspect_packet(packet_path, submission_root=None,
expected_packet_sha256=None)`. The expected digest, when supplied, is an
independently provided SHA-256 of the actual packet bytes. A packet's own claims
are not a signature or a qualified-envelope attestation. Optional
`submission_manifest` is compared with the exact inspected file hashes; matching
that manifest still establishes no theorem or source/artifact correspondence.

```sh
python3 -B tools/verification/preflight.py --packet work-packets/VJ-009.json
```

Current templates return INFRA/NOT_READY (exit 3). Established structural scope,
identity or metadata contradictions return REJECT (exit 2), scoped to preflight
data policy rather than a Lean theorem judgment. Missing/unreadable required
inputs return INFRA. Even a superficially complete forged Ready packet returns
INFRA/FULL_GATE_UNIMPLEMENTED; there is no route to automatic proof admission.
Manual-review classes require their frozen review policy instead of fabricated
Lean evidence.

For regression tests, allocate scratch explicitly and set
`VERIFIED_JSON_TEST_WORK` to that existing directory before running
`python3 -B -m unittest discover -s tests/verification`. The tests inspect benign
fixtures and hostile metadata; they do not execute submitted Lean code.

## Reuse and remaining qualification

Reuse the public [comparator](https://github.com/leanprover/comparator),
[lean4export](https://github.com/leanprover/lean4export), and an independently
implemented checker such as [nanoda](https://github.com/robsimmons/nanoda_lib).
Their source licenses are Apache-2.0. No private corpus checker implementation is
copied into this repository. VJ-051–VJ-053 require exact source/toolchain pins,
current artifact formats, primitive/string/byte footprint probes, and a real
positive/negative envelope qualification before community mathematical tickets
become Ready.

The preflight explicitly marks these stages UNIMPLEMENTED: authenticated
qualified-envelope binding; isolated candidate elaboration and descendant
teardown; frozen declaration/meaning comparison; transitive axiom audit; official
kernel replay; independent kernel replay; and fresh integration rebuild. A local
trusted bootstrap tool build or reference proof replay does not qualify those
stages for adversarial community submissions.

The eventual supervisor must construct trusted challenges and mappings,
establish real sandbox denial, kill all candidate descendants, seal artifacts,
and check bounded exported data outside the untrusted worker. Upstream process
exit conventions require explicit INFRA versus proof-rejection adaptation.
Unsupported current Lean features or independent-checker string/byte semantics
remain named blockers. No unsandboxed candidate build is a Green community gate.

## Trusted maintainer replay experiment

`bootstrap_replay.py` can inspect the fixed current core roots in an already-built,
explicitly trusted maintainer workspace. It requires an independently supplied
SHA-256 for a tool manifest binding the exact compiler source identity and all
four fixed-role binary hashes. It uses the selected Lean distribution's
`leanexport`, `leanchecker-paranoid --from-export`, and bundled `nanoda_bin`;
there is no argument-vector override or tool download. The primitive export basis
comes from the pinned public comparator. All process exits and log identities are
retained in a fresh caller-allocated work directory.

The adapter deliberately reports `completed`/`not-established` observations,
never community PASS. The caller must establish a fresh trusted source/build
correspondence before invocation. Its `--trusted-bootstrap` acknowledgment is an
operational precondition, not authentication of an adversarial submission. Do
not run it on untrusted objects: exporters/object readers and execution of their
initializers are not contained by this adapter. No data from this experiment can
activate an unqualified packet. The full supervisor, isolation, target comparison
and independent qualification remain pending.

`rc4-bootstrap-tools.json` records the measured Darwin arm64 release and binary
identities. It is explicitly an unqualified bootstrap descriptor, not permission
to run community code. The current 17 source roots were exported and replayed by
the official and independent kernels in a frozen local experiment. A deliberate
`debug.skipKernelTC` false-proof canary was rejected by both. This does not prove
the reviewed JSON capstones or machine-code correspondence.

A broader String-literal positive currently fails native serialized replay with
an unavailable implicit `String.ofList` dependency, even with that primitive
requested in the export. That input is an infrastructure/ordering qualification
gap, not a refuted theorem. Nanoda's successful typecheck logs also contain an
axiom pretty-print diagnostic. Keep these limitations visible and qualify the
actual needed footprint before advertising a complete submission envelope.

## Audit-repair identity and lifecycle

Root manifests and source bindings are required for bootstrap checks. The caller
can pin the source-files-map digest independently. Builds/tests use a copied
verified source snapshot; receipts record manifests, source dependencies, features,
compiler versions and native artifact hashes. Neither self-reported hashes nor
a trusted snapshot are authentication of hostile candidate code.

The replay command now requires source/root-manifest pins, includes DocumentSpec
in its fixed import set and exports explicit meaning roots. The contract manifest
names Document/FitsLimits/Utf8Text as well as its witnesses. This supplies a public
recipe for the new roots; it does not turn witnesses into parser conformance.

Process execution uses nonblocking streams, bounded output/deadline/drain, and
non-reaping exit observation. Failure cleanup signals before direct-child reap.
Normal exited+EOF completion does not signal its group and does not establish
absence of silent descendants. Sole-reaper/no-auto-reap ownership is required;
failed or unobserved cleanup is infrastructure. No sandbox is commissioned.

Packet integer conversion is bounded locally and parser ValueError is translated
to structured INVALID_JSON; the interpreter's global conversion guard is preserved.
