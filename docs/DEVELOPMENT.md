# Verified JSON development plan

Build a fresh Lean reference from independent reviewed definitions, then prove parsing, serialization and numerical contracts. Existing implementations help identify APIs and edge cases; they are comparison targets rather than the definition of correctness. The first release delivers the verified source core and offline differential CLI. Runtime caching, production feedback and proved Rust acceleration come later.

The repository owns the public specification, proof coverage and package releases. Native GitHub issues and Project views coordinate contributors. Immutable work packets define tasks; there is no new tracker, database or claim service in the initial setup.

## Development phases

| Phase | Product | Acceptance before advancing |
| --- | --- | --- |
| P0 Project and tool baseline | Exact Lean stable/RC pins, repository layout, source provenance, candidate dependency slice | Naming/ownership and installation gates; effective compiler identity protected |
| P1 Reviewed contract | Wire AST, independent document relation, profiles, outcomes, budgets, neutral protocol | Human semantic review, explicit theorem roots and non-vacuity examples |
| P2 Verified vertical slice | Byte cursor, scalar/token parsers, protocol prototype and one comparison | Qualified submission gate first; fresh proof artifacts; positive and negative cases; reproducible synthetic discrepancy |
| P3 Complete JSON core | Unicode/escapes, arrays/objects, complete-document parser, serializer/profile checks | Soundness, supported-domain completeness, termination, cost/bounds, AST round trip and public API/codec binding |
| P4 Binary64 | Minimum FloatLib slice and JSON-number bridge | Arbitrary supported decimal conversion, signed zero, ties, underflow and range behavior proved; no formatter-only shortcut |
| P5 Differential CLI | Pinned Rust profiles, corpus, generators, classification and shrinkers | Seeded faults detected; permitted differences classified; minimized cases independently replay |
| P6 Public alpha or RC | Reproducible source package and CLI, coverage and trust manifest | All release blockers resolved; current toolchain replay; qualified package and supported-platform installation |
| P7 Checked runtime | Bounded oracle transport and approved-result cache | Every returned result approved or checked; resource/fault tests; measured unique-input workload cost |
| P8 Feedback and repair | Local repro queue, isolated patch candidates and reviewed reporting | Privacy, deduplication, reproducibility and external authorization gates |
| P9 Proved Rust fast paths | Selected source-to-model refinement proofs | All-input property on named domain; exact deployed identity; genuine fallback outside that domain |
| P10 Stable ecosystem release | Stable semantic/API versions and maintenance | Downstream qualification and migration policy; manual publication after stable-pin checks |

P0/P1 infrastructure and contract work precede opening proof tickets to the public. P4 dependency inspection can overlap grammar implementation, but the JSON byte grammar need not wait for numerical library admission. A numeric compatibility claim requires P4 even if an exact-token core is released earlier.

## Core semantics

Input is an immutable byte sequence, including malformed input. The parser accepts exactly one document with JSON whitespace around it. The wire AST retains ordered object members and duplicates, number tokens and decoded UTF-16 units. Strict scalar and duplicate-key validation are separate profile rules. Byte-identical document reconstruction is a separate operation because whitespace and escape spelling may be discarded.

Candidate comparisons specify their projection: a map that collapses duplicates or a numeric conversion that rounds a token cannot certify lossless wire semantics. Binary64 comparisons use bit patterns rather than approximate numerical equality. Limits, unsupported conversions and infrastructure failures are distinct from syntax invalidity.

Proposed default budgets are 1 MiB input, nesting depth 128, 100,000 total AST values/member entries, 4,096 bytes per number token and 8 MiB serialized output. They remain proposed until the contract review validates their precise counting and serializer/parser compatibility. Operational oracle-request caps such as 2 seconds and 256 MiB are starting qualification targets, not proved parser performance. Proof-build and replay worker budgets are separate, packet-specific limits. Abstract work counters are defined with the cost model. A wall-clock timeout is infrastructure failure rather than invalid JSON.

## Claim coverage

| Roots | Required scope |
| --- | --- |
| J01–J04 | Bounds/progress, UTF-8, escape semantics and exact number-token grammar |
| J05–J08 | Arbitrary-input parsing soundness, completeness within explicit profiles/budgets, termination and modeled resource use |
| J09–J11 | Well-formed AST serialization, compatible-budget round trip and strict profile validation |
| J12–J13 | Correctly rounded supported decimal-to-binary64 conversion and finite serialization contract |
| J14 | Explicit candidate representation projection/preservation scope |
| J15 | Approved-result cache model and concrete trust/refinement boundary |
| J16 | Exact public API/outcome binding to specification and deployed identities |
| J17 | Lossless neutral transport independent of the JSON candidate under test |

The root statements and meaning-bearing definitions are maintained independently of proof scripts. The specification cannot merely call the implementation and define that result as correct. Each root has constructive witnesses and adversarial cases. Parser success and serializer-generated inputs alone cannot justify complete arbitrary-input correctness.

## Contributor task classes

| Class | What can change | How it is accepted |
| --- | --- | --- |
| Proof only | Authorized proof bodies/helper proofs | Frozen target/dependency comparison plus transitive axioms and kernel replay |
| Implementation with proofs | Explicit named implementation holes and authorized proofs | Independent frozen contract; total correctness obligations; runtime correspondence review where needed |
| Tests and documentation | Named fixtures, coverage or prose | Reproducible behavior checks and semantic review; no automatic proof claim |
| Contract or numerical semantics | Proposed specification/type/profile changes | Human review and revised immutable packet before proof work |
| Infrastructure or release | Verifiers, build/CI, approval and packaging | Independent boundary review and positive/negative qualification |

When a large task exceeds a useful reservation, split it into native sub-issues. Each issue points to a bounded packet; dependencies use native blocked-by links. The [ticket index](TICKETS.md) records the planned breakdown. Machine-readable templates do not grant readiness or claim authority.

## Native GitHub setup

Create milestones for the phases and a Project board with Draft, Blocked, Ready, Claimed, In Progress, In Review and Done. Use native assignees, dependencies, sub-issues and linked PRs. Add fields for packet ID/revision, task class and an optional Claim Expires UTC text value. Issue comments record the precise acknowledged six-hour deadline because date fields are not a sub-day lease mechanism.

Use GitHub's built-in add/status workflows where they match the project's lifecycle. A closed issue or Done card is coordination state; the proof-coverage manifest remains authoritative for what was established. A task is Ready only after maintainers freeze its contract/dependencies and qualify the validator. No automatic claim action is enabled initially.

## Lean and numerical dependency maintenance

Use a current official Lean RC for forward development and the latest stable release for compatibility and stable publication. Each packet pins exact identities; contributors do not update the toolchain themselves to make a task compile. Qualification jobs prepare upgrades, compare elaborated types and definition/instance closure, rebuild proofs and current native artifacts, replay the accepted closure and run affected fixtures.

Use only necessary FloatLib modules and declarations, measuring the transitive imported and executable closures. Protect the project compiler pin during dependency resolution. Small compatibility patches remain an explicit upstream-base overlay with license, changed definitions/statements and replay evidence. A numerical semantic repair needs separate review; it is not a routine tactic cleanup.

Stable promotion from a project RC creates a fresh exact stable toolchain/package candidate and rechecks it. GitHub's manual workflow UI performs publication only after qualification and release approval. Published package versions are immutable; an RC is not relabeled to hide its original compiler identity.

## Verification infrastructure first

Qualify existing Lean submission comparator/replay tools before opening auto-verifiable work. [Submission verification](VERIFICATION.md) defines the gate. It checks the exact trusted target and transitive meaning/axioms, not just source spelling. Untrusted elaboration runs away from credentials, and a separate trusted verifier receives sealed output after worker termination.

Formatting scripts may improve presentation. They cannot remove a missing proof, alter a hypothesis, rewrite a definition, silence a failure or declare a placeholder clean. Successful proof-generation and cleanup are different operations.

## First collaboration launch

The launch milestone is a reviewed small contract, qualified checker canaries, several genuinely Ready scalar/byte proof packets and a reproducible oracle/adapter comparison. Publish the task scope, validation command, expected artifacts and source version so another person's LLM can work without private tooling or credentials. A seeded synthetic discrepancy is an adequate first demonstration; upstream bugs are useful outcomes rather than a required publicity statistic.
