# Community submission and release verification

**Design proposal — unimplemented.** This document specifies a reusable submission checker for the verified JSON project. It is repository-ready documentation, not an operational service or a verified implementation of the checker. Contributor commands below are proposed interfaces and must not appear as working instructions until the qualification ticket implements and tests them. Tool research and limitations are in [TOOL-ASSESSMENT.md](TOOL-ASSESSMENT.md).

## Meaning of a passing submission

A proof ticket passes when its exact frozen target declarations and referenced specification definitions match, its complete selected proof closure uses only approved axioms, its artifacts are tied to the submitted source, and all required qualified kernels accept. An implementation ticket additionally passes an independent contract-coverage review and executable/refinement gates. A PASS is scoped to the ticket revision, candidate bytes, dependency/compiler envelope, and declared properties; it is not a universal certification of every file in a contributor's repository.

AI-generated source is treated as untrusted input. This classification does not require a claim about a contributor's motives. Lean elaboration can execute arbitrary metaprograms, and proof checking is distinct from checking the intended specification.

## Ticket contract and protected inputs

This Lean gate covers proof-only and implementation-with-proofs tickets. Maintainer contracts, checker bootstrap, tests and documentation use their own reviewed acceptance policy; they can become Ready without a fictitious Lean theorem or a self-certifying checker. Their packets record nonapplicable Lean fields with an explicit reason and cannot claim automatic mathematical acceptance. All templates in this scaffold remain unready.

A maintainer-generated packet binds:

- Stable ticket ID, revision, proof-only or implementation-with-proofs class, dependencies, selected API profile, and exact repository/base source identity.
- Reviewed target names, declaration kinds, complete elaborated types, universe parameters, and invariant specification definitions/instances/inductives with their source and declaration identities.
- The explicit mutable definition-hole list; empty for proof-only work. No inferred permission from an occurrence of `sorry`.
- Exact compiler selector, dependency source/compiled identities, module allowlist, verifier/exporter/checker/supervisor identities, maximum axiom set, resource policy, and required canaries.
- Required theorem roots, behavioral and non-vacuity witnesses, fresh build targets, artifact/evidence outputs, and owned candidate paths.

Until the exact current-Lean envelope and end-to-end interface are qualified, the packet's operational field is **`validator.argv: null`** and its validator status is **`NOT_READY`**. No illustrative command in documentation substitutes for that field. After qualification, a READY packet publishes the exact argument vector and generated workspace; contributors invoke those bytes rather than inventing a local substitute. Command arguments and paths are data, never shell-interpolated code.

The contributor's PR changes only the repository paths and declaration holes authorized by the frozen packet. A trusted generator maps those changes into an isolated submission workspace, which may use `Submission.lean` and permitted helper modules under `Submission/`. Those generated names are a worker layout, not permission to ignore the actual allowed repository paths. Contributors do not control the challenge, bridge, spec, ticket manifest, checker code, configuration, toolchain, dependency lock, build scripts, native plugins, or CI policy. Sources outside the packet's allowed paths are rejected before elaboration. Source-tree traversal rejects unexpected file kinds, path traversal, and links that escape the input root.

A maintainer generator may put `sorry` into selected bodies of an isolated **challenge artifact** for statement comparison. Such stubs never belong to the product or shipping dependency closure. The generator must preserve the actual elaborated specification and explicitly named holes. Never use a global text replacement, regex, or script that blindly removes `sorry` to create an alleged complete implementation.

## Two contribution classes

| Gate | Proof-only ticket | Implementation-with-proofs ticket |
| --- | --- | --- |
| Frozen source | All specification and executable definitions stay identical; only designated proof bodies and namespaced helper declarations may vary. | All specification definitions stay identical. Only explicitly listed implementation bodies may vary; their type/safety/universe metadata stays fixed. |
| Target comparison | Exact theorem statement and referenced constant graph; no definition holes. | Same comparison with a signed explicit definition-hole list. Every hole must appear in the independent reviewed behavioral/refinement contract. |
| Main result | Proof of the unchanged target using allowed axioms. | Total soundness/completeness/refinement and budget/termination theorems for the intended input domain, rather than mere function typing or one-direction soundness. |
| Runtime work | No new runtime path or replacement accepted through this class. | Audit totality, executable closure, compiled substitutions, FFI, serializer/comparison/destruction paths, and actual release tests. |
| Review | Human attention focuses on packet/spec meaning, non-vacuity, and changed helper/trust boundaries. | Review contract adequacy and executable/refinement correspondence, including performance/resource implications. |

For example, a parser that rejects every input can satisfy a one-direction soundness theorem. Each parser implementation ticket must also require completeness for an independently defined supported language/budget and informative success witnesses. Likewise, a numeric ticket must state complete word/sign/overflow outcomes rather than equality over real numbers alone.

## Reusable checker architecture

1. **Freeze trusted inputs.** The supervisor reconstructs challenge, bridge, config, tools, and admitted dependency closure from the packet's verified bytes. It validates current ticket revision and candidate source identities. It never relies on contributor-produced PASS text or receipts.
2. **Prepare an isolated compiler worker.** Provide only the frozen source, read-only tool/dependency image, and fresh writable output space. No credentials, repository administration token, network, unreviewed native plugin, shared writable dependency cache, or arbitrary host filesystem. Resource limits cover CPU time, wall time, memory, processes, disk, output, and input sizes. Prove through real probes that the configured sandbox is active; unsupported containment is INFRA before any candidate runs.
3. **Elaborate only in that worker.** Candidate initialization, macros, tactics, attributes, and imports are all contained there. Build the exact generated solution bridge using the fixed build description. Record fresh compiler exit and produced artifacts; missing/stale artifacts are not success. A restricted source scan helps explain refusals but does not replace elaborated-environment inspection.
4. **End the entire untrusted process tree and seal outputs.** The supervisor terminates and confirms the absence of all candidate descendants before taking outputs. Copy/hash owned outputs into verifier-controlled immutable evidence. Export the bounded declaration closure inside a disposable isolated export worker, with the source/object/export correspondence recorded. No untrusted writer can modify an artifact during export or checking.
5. **Use a separate trusted verifier.** It sees bounded serialized proof data and supervisor-authenticated metadata, not the contributor's runtime environment or executable plugins. Validate export structure and references; compare the target and full referenced constant graph against the independently created trusted challenge. Verify core primitive identities and selected imported definitions from the pinned toolchain. Treat the export parser/checker as a security boundary with its own resource controls.
6. **Audit transitive axioms and declaration coverage.** Default maximum set is precisely `propext`, `Quot.sound`, and `Classical.choice`; individual tickets may be stricter. No `sorryAx`, user-defined axiom, generated native-computation axiom, or widened policy. Check every required target and every submitted product/helper declaration that could enter the product. A helper outside the capstone closure is not thereby exempt from the product's no-placeholder policy.
7. **Replay through qualified kernels.** The official kernel replay and a supported independently implemented checker must both actually inspect and accept the frozen closure. Neither an elaborator success nor a skipped independent layer constitutes this gate. A checker with an unsupported object/export version, inductive feature, primitive extension, or missing executable reports INFRA; the pipeline never silently downgrades the check.
8. **Apply contribution-class gates.** Proof-only submissions must preserve all frozen definitions and types. Implementation submissions run the total contract/non-vacuity and runtime gates above. Record correspondence from accepted definition bodies to the production source that will be integrated.
9. **Rebuild the shipping product independently.** Incorporate the accepted source through a maintainer review, remove challenge-only namespace/files from shipping targets, rebuild fresh, and audit product declarations and complete public API/refinement roots. Recheck affected aggregate capstones and dependencies. An individually passing ticket is not yet a release.

The initial implementation should adapt comparator interfaces and exports, not write another untested theorem-comparison algorithm. The supervisor and structured evidence wrapper are additional software that requires explicit tests and independent review. Native object loading, exporter behavior, serialized-input parsing, external checker invocation, and their limits remain part of its trust manifest.

## Native evaluation and compiler substitutions

Compiler-backed `native_decide`, native variants of decision tactics, and direct trusted-native computation bridges are outside the default proof policy when they introduce extra axioms. Ordinary kernel-checked `decide` and proof-producing automation remain permitted when their complete axiom closure satisfies the packet. Current Lean versions can create per-computation axioms, so the authoritative check is the transitive axiom graph, not a search for one keyword such as `Lean.trustCompiler`. Older-toolchain fields must not be copied into a new checker configuration as if their semantics were unchanged.

For implementation tickets, reject new project-owned `unsafe`, `partial`, unchecked `implemented_by`, foreign `extern`, or executable `noncomputable` paths through the ordinary contribution gate. A deliberately reviewed extension can change this policy only through a separate trust-boundary ticket. Legitimate compiler-generated recursion shims need pin-specific recognition and a total reference-definition correspondence; their name alone is not a blanket exception.

Inspect compiled-environment attributes and actual code-generation reachability, as well as source syntax. A macro can add an attribute that a keyword scan misses. Approved standard-runtime primitives and unavoidable trusted foreign implementations remain explicitly listed exceptions. Proved `csimp` refinements reduce the substitution obligation but do not formally verify the compiler, linker, runtime, operating system, or hardware.

## Verdicts and evidence

These are proposed wrapper verdicts. Existing third-party exit conventions must be adapted and tested; do not grep stdout for `error:` or turn every nonzero process exit into “proof rejected.”

| Verdict | Meaning | Examples |
| --- | --- | --- |
| PASS | Every declared required stage actually examined the exact artifacts and accepted; all outputs/evidence are present and current. | Unchanged target, approved closure, valid source/artifact correspondence, native plus independent replay, completed class-specific gates. |
| REJECT | A functioning qualified stage established an actual candidate policy/type/proof/contract violation. | Wrong target or referenced definition; unauthorized paths/imports; missing submitted declaration after complete environment resolution; disallowed axiom; a checked proof term rejected by a supported kernel; a reproducible contract violation. |
| INFRA | The pipeline could not establish the required judgment. It carries no mathematical verdict. | Timeout/resource exhaustion; tool missing; sandbox inactive; unsupported export/inductive/version; unresolved trusted module; stale artifact; checker crash; failed write; uncertain descendant teardown or correspondence. |

A compile error is REJECT only when the compiler successfully resolved the packet environment and identifies a candidate defect. A dependency-resolution/build-driver failure is INFRA. If one stage conclusively rejects while another has an infrastructure failure, preserve both results; the submission cannot PASS and its disposition records the confirmed rejection plus incomplete check scope.

The trusted receipt includes ticket/revision, candidate/source hashes, original trusted challenge and generated bridge hashes, compiler/dependency/module/checker policy identities, target census, axiom sets, artifact/export hashes, every stage's `performed` status, exit/result classification, bounded diagnostic/evidence hashes, resource use, and final contribution-class result. The receipt is emitted by the separate supervisor, never by candidate code. A cache key includes all these semantic/build inputs; toolchain/spec/dependency changes require fresh namespaces and revalidation.

## Qualification canaries

Use real end-to-end submissions, not only mocked success responses. Each negative case is paired with a valid positive using the same toolchain/module footprint; otherwise a blanket refusal could look like protection.

| Canary | Required outcome |
| --- | --- |
| Valid small proof and valid total byte helper implementation | PASS through all declared stages. |
| Direct `sorry`, `admit`, or `sorryAx`; hidden placeholder in imported local helper | REJECT, with the actual dependency exposed. |
| Custom axiom hidden behind a helper; native-computation proof axiom | REJECT even when elaboration succeeds. |
| `debug.skipKernelTC` adds an unchecked false proof | At least one replay layer actually rejects; axiom-print output alone must not pass it. |
| Changed theorem type, binder/universe, frozen spec definition, instance, inductive or primitive | REJECT exact-target/dependency comparison. |
| Weakened implementation specification; reject-everything parser under an inadequate one-way contract | Qualification audit catches insufficient contract; ticket does not open until completeness/non-vacuity is repaired. |
| Contributor widens definition-hole list/axiom allowlist or edits checker/bridge/config | REJECT before candidate execution. |
| Candidate filesystem/network/secret read attempt, symlink escape | Boundary denies it and probe verifies denial, including unrelated sentinels and positive owned-output write. |
| Detached process races object/export changes after compilation | Supervisor confirms all descendants gone; untrusted bytes cannot change sealed artifacts. Failure to establish this is INFRA. |
| Trusted tool override points into writable candidate tree | REJECT configuration; no candidate-controlled verifier binary runs. |
| Missing checker, incompatible `.olean`/export, unsupported kernel feature, failed output write | INFRA with named cause, never mathematical REJECT or PASS. |
| Stale object, forged PASS logs/receipt, zero-target manifest, wrong artifact hash | Cannot PASS; classify established forgery as REJECT and missing/unobserved evidence as INFRA. |
| Source macro adds unchecked runtime substitution despite clean theorem proof | Implementation gate REJECT; proof checking alone cannot certify runtime behavior. |
| Pinned kernel-arena cases including known projection/recursor and literal/primitive edge cases | Expected accepted/rejected/declined outcomes on actual exact checkers. Never reinterpret “either” or unsupported cases as negative proof evidence. |

Qualification includes supported strings/byte arrays/integers and the minimal admitted FloatLib numeric slice, not merely arithmetic examples. Repeat it whenever Lean, Lake, exporter, comparator, independent checker, sandbox/supervisor, dependencies, or build policy changes. Newest Lean including RCs is a rolling qualification objective: each active ticket remains frozen to one qualified version. A newer RC lacking a required checker cannot receive a PASS until that support is established.

## Existing upstream command versus proposed project interface

**Proposed wrapper — unimplemented:** use a single repository-owned `tools/verify-ticket` adaptation, not a new product CLI. Its acceptance contract takes a packet, allowed source submission root, allocated output/work destination, and machine-readable verdict destination. An illustrative spelling is:

```sh
# Proposed only; validator.argv stays null until qualification.
tools/verify-ticket --packet work-packets/TICKET_ID.json \
  --submission "$TICKET_SUBMISSION_WORK" \
  --work "$TICKET_VERIFY_WORK" --json "$TICKET_VERIFY_WORK/result.json"
```

The packet's exact READY `validator.argv` is authoritative once implemented; final argument names may differ from this proposal. The wrapper generates the trusted challenge/bridge/config itself, adopts the qualified existing comparator/replay code, and exposes PASS/REJECT/INFRA. It neither trusts a source-controlled shell command nor evaluates arbitrary repository setup scripts.

**Existing upstream command:** lean-eval's generated comparator workspaces use `lake test`. That command invokes the generated protected test harness and its separately installed comparator/exporter/sandbox/independent checker. It is evidence of a reusable architecture, not an immediately available acceptance command for this planned JSON repository. [Upstream solver workflow](https://github.com/leanprover/lean-eval#quick-start-for-solvers)

`TICKET_SUBMISSION_WORK` and `TICKET_VERIFY_WORK` are distinct contributor-selected scratch destinations. The future checker creates only owned generated/build/evidence paths and preserves prior failed evidence; it does not silently run setup hooks, download mutable dependencies, or clean unrelated files. Maintainers publish supported platform/setup instructions only after the envelope is qualified. The acceptance worker initially targets a supported isolated Linux environment; native editor or unsandboxed local build feedback is advisory. Six-hour claim expiry affects coordination, not theorem truth; submitting or rechecking work still binds the exact packet revision and source identity. Native GitHub claim coordination and proof checking remain separate mechanisms.

The solver instructions should say: preserve the target declarations, implement only listed holes, use allowed imports, return source plus a concise explanation, and report a specification/toolchain blocker instead of weakening assumptions. They should allow kernel-checked normal proof automation and prohibit attempts to manipulate the checker environment. An LLM can generate proof scripts freely within these constraints; its claims of local success remain advisory until the neutral checker runs.

## Release acceptance

Release verification covers every enabled public API capstone, implementation/refinement root and shipping declaration, with no generated challenge or placeholder dependency. A core/oracle/comparison release checks its compiled oracle, Rust adapter/comparator, neutral protocol, resource limits, replay corpus and exact build manifest. Binary64 claims additionally require numerical public-API and compiled-oracle binding evidence. Cache and checked-runtime correctness are mandatory only when those optional runtime claims are enabled; an exact-token core release does not inherit them. Unqualified claims remain explicitly disabled. Proof-only ticket PASS, implementation-ticket PASS, integration PASS and release PASS are separate scopes. None automatically creates a repository commit, merges a PR, publishes artifacts, or reports upstream issues.
