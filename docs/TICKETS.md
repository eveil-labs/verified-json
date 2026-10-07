# Contributor backlog and immutable packet templates

Status: candidate planning documents, 2026-10-07. No repository, issue, PR, Project, claim, workflow or artifact release has been created. Every target source pin, declaration binding and qualified validator command is absent. All 55 templates have `claim_ready: false`. File paths below are prospective public-repository paths.

This backlog expands the audited P0–P10 project plan into bounded work units. The matching `../work-packets/TICKETS.json` is a full machine-readable template index; it is not a tracker and does not establish that any Lean declaration or gate already exists. The source-plan digest is `07ab8c2bbb1ec40070aa7bdf96cffa2b9bffd9726a051b523af8313c5a915fd3`.

## Native GitHub coordination

Use one native phase parent issue for each P0–P10, with individual ticket issues as sub-issues. Use native blocked-by relationships for the dependency DAG, labels for ticket class and claim roots, assignees for the acknowledged contributor, and a Projects table/board for readiness and progress. Projects is the dynamic coordination view; committed work-packet files are the immutable task contract. Issue prose links to exact packet revision/path/digest rather than replacing it. GitHub supports these native relationships and project views. [Sub-issues](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/adding-sub-issues), [dependencies](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/creating-issue-dependencies), [Projects](https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/about-projects)

Board states: Draft, Blocked, Ready, Claimed, In Progress, In Review, Done. Done is coordination state, not a theorem acceptance record. Maintainers reconcile these manually with the pinned packet and merged prerequisite evidence. Closing an issue or moving a card does not establish a theorem or release result.

A contributor asks for a six-hour courtesy reservation in a comment identifying the immutable packet. A maintainer checks readiness, acknowledges it, assigns the issue, and records UTC start and expiry. Six hours is a reservation interval, not a promise the work can be completed in that time. Releasing, renewing, expiring and reassigning work are manual; existing candidate bytes and open PRs remain attributable after a reservation expires. A submitted PR does not automatically renew a reservation or confer merge authority. The next contributor checks prior work and uses a separately acknowledged handoff. No bot commands, Actions claim bot, bespoke claim database or live reservations are introduced.

`leanprover-community/intentions` is only an optional-deferred candidate. Its documented hour-duration support could be useful later, but exact revision, permissions, six-hour sweep behavior and PR/In Progress transitions need qualification before adoption. It is not part of the immediate backlog. [Intentions](https://github.com/leanprover-community/intentions)

## Making a ticket claimable

A maintainer first creates or adopts actual source declarations for mathematical tasks, reviews their meaning, and seals one committed packet. Proof/implementation packets must bind:

- Exact repository commit/tree and permitted files/selectors.
- Independently reviewed specification/profile/budget and top-level theorem types.
- Semantics-bearing definition/instance closure and exact input/output/public API bindings.
- Exact toolchain/dependencies, import/axiom policy, validator commands, checker identities and required artifacts.
- Merged accepted prerequisite commits, constructive witnesses and targeted negative/mutation fixtures.
- A feasible six-hour scope and independent reviewer. If scope cannot be rehearsed as one reviewable unit, split it into successor sub-issues before reservations open.

Required nullable fields must be filled with actual identities for the task's acceptance class. Desired J-root labels are not declaration names. Bootstrap, contract review and documentation tasks instead freeze their human review checklist and applicable tests, with mathematical fields marked not applicable for a stated reason; they do not require the not-yet-built checker to accept itself. A populated JSON card, a green source-text check, or an LLM assertion cannot set a proof ticket ready. Lookup existing declarations by name, statement and module before assigning a proof. The future entry point is `tools/verify-ticket`, qualified against the gate contract; this document does not invent an installed command or a new verification product.

## Ticket classes and submission boundaries

- **proof-only:** edit only sealed proof bodies and approved helper scope. Existing theorem types, hypotheses, implementation bodies, meaning-bearing definitions/instances and bindings stay frozen. A difficult goal becomes a blocker rather than a weaker theorem.
- **implementation-with-proofs:** edit only the sealed implementation body/module scope and scoped proof artifacts. The independently reviewed specification, profiles and public target statements stay frozen. New APIs or semantics need a separate contract packet.
- **maintainer-contract-release-infrastructure:** contributors may prepare scoped proposals, but semantic, checker, native boundary, CI, dependency, licensing and release changes need designated independent maintainers. This class does not imply that all its Rust/tool code is formally proved.
- **tests-docs:** change sealed public/synthetic fixtures or documentation, preserving contract and expected-category identities. Passing tests never upgrades an empirical or native boundary into an all-input proof.

An LLM can help draft code/proofs, but the contributor remains responsible for allowed diffs and honest evidence. Every submission records exact packet identity, changed files, checker exits/artifacts, declaration/meaning drift results, axiom/replay results, targeted tests, remaining limitations and handoff state. Infrastructure failures remain infrastructure failures. Builders cannot approve their own semantic or gate changes.

## Gate contract

- **G00 — Frozen inputs/readiness:** Task-class-specific frozen source, scope and applicable acceptance identities exist. Mathematical classes need actual target/compiler/dependency/validator bindings; bootstrap/review classes use approved manual checklists and explicit nonapplicability reasons.
- **G01 — Fresh build/artifact verdict:** Pinned commands complete with correct exit codes and newly produced expected artifacts; missing checks and infrastructure errors cannot pass.
- **G02 — Meaning and binding preservation:** Compare elaborated target types, hypotheses, semantics-bearing definitions/instances, input/output bindings and public-root mappings against frozen accepted records; textual names alone are insufficient.
- **G03 — Axiom/native boundary audit:** Named roots and transitive proof dependencies satisfy the reviewed axiom basis; no placeholder/custom axiom or unproved native substitute gains a proved claim.
- **G04 — Replay:** Fresh kernel replay and supported independent checker evidence cover the sealed closure; unsupported/incompatible checker is an explicit infrastructure gap.
- **G05 — Existing-declaration reuse:** Before sealing proof work search the declaration index by name, statement and module; bind qualified existing results rather than reproving them.
- **G06 — Nonvacuity and adversarial fixtures:** Constructive witnesses, syntax/profile/limit negatives and scoped mutants validate root premises and error-category distinctions.
- **G07 — Allowed diff:** Only packet-allowed files/selectors changed; proof-only edits preserve all existing declarations/implementation/meaning, implementation-with-proofs edits preserve independently reviewed spec and root types.
- **G08 — Scoped empirical checks:** Relevant tests/corpus/protocol/package evidence matches exact builds and profiles; it is not labeled an all-input proof.
- **G09 — Independent acceptance:** Builder does not approve its own semantic, checker, CI, release or native-boundary changes; unresolved blockers prevent acceptance.

## J01–J17 coverage

These are intended capstones, not claims that theorems exist. Capstones become small composition tickets only after their supporting modules and frozen targets are available. J14 and concrete native cache/transport boundaries may remain explicitly trusted/tested where the project plan permits; empirical results do not count as discharged proof roots.

| Root | Intended obligation | Main tickets |
| --- | --- | --- |
| J01 | Byte/cursor bounds | VJ-009, VJ-010 |
| J02 | UTF-8 scalar relation | VJ-017, VJ-018 |
| J03 | Wire escape preservation | VJ-019 |
| J04 | Exact number grammar | VJ-012, VJ-021 |
| J05 | Independent parsing soundness | VJ-024 |
| J06 | Profile/budget completeness | VJ-025 |
| J07 | Termination | VJ-026 |
| J08 | Modeled resource bounds | VJ-027 |
| J09 | Valid serializer output | VJ-029 |
| J10 | Semantic AST round trip | VJ-030 |
| J11 | Scalar/duplicate profile validation | VJ-020, VJ-028 |
| J12 | Arbitrary supported decimal rounding | VJ-035, VJ-036, VJ-055 |
| J13 | Finite float serialization | VJ-037, VJ-055 |
| J14 | Adapter preservation or explicit tested boundary | VJ-016, VJ-038 |
| J15 | Approved cache result model | VJ-044 |
| J16 | Public API contract and concrete boundary | VJ-032, VJ-045, VJ-048, VJ-055 |
| J17 | Neutral transport preservation | VJ-031, VJ-055 |


## Bootstrap gate ordering

VJ-054 prepares the package skeleton. VJ-051 qualifies existing comparator/replay tools; VJ-052 implements the bounded supervisor; VJ-053 runs actual positive/negative gate qualification. These are independently reviewed infrastructure tasks, not proofs validated by their own unbuilt checker. Every mathematical packet depends on VJ-053 and VJ-054. VJ-042 later extends release mutations; it is not the first submission gate. VJ-055 binds admitted binary64 modules into the exported oracle before numeric claims are enabled.

## Ticket index

Prerequisites are accepted artifacts, not merely closed issues. All templates remain unready.

| ID | Phase | Class | Bounded task | Prerequisites |
| --- | --- | --- | --- | --- |
| VJ-001 | P0 | maintainer-contract-release-infrastructure | Select project ownership, names and provenance policy | — |
| VJ-002 | P0 | maintainer-contract-release-infrastructure | Freeze stable and development Lean lane candidates | VJ-001 |
| VJ-003 | P0 | maintainer-contract-release-infrastructure | Prepare native GitHub six-hour courtesy reservations | VJ-001 |
| VJ-004 | P1 | maintainer-contract-release-infrastructure | Prepare frozen-packet and Lean acceptance gate contract | VJ-002 |
| VJ-005 | P1 | maintainer-contract-release-infrastructure | Review wire AST and independent JSON relations | VJ-001, VJ-002 |
| VJ-006 | P1 | maintainer-contract-release-infrastructure | Review budgets, results, profiles and public API predicates | VJ-005 |
| VJ-007 | P1 | maintainer-contract-release-infrastructure | Review independent neutral transport and comparison contract | VJ-005, VJ-006 |
| VJ-008 | P1 | maintainer-contract-release-infrastructure | Create claim-root ledger and concrete packet sealing procedure | VJ-004, VJ-005, VJ-006, VJ-007 |
| VJ-009 | P2 | implementation-with-proofs | Implement bounded byte cursor read primitives | VJ-005, VJ-006, VJ-008, VJ-053, VJ-054 |
| VJ-010 | P2 | proof-only | Prove cursor advance and checked-length arithmetic bounds | VJ-009, VJ-053, VJ-054 |
| VJ-011 | P2 | implementation-with-proofs | Implement whitespace and fixed literal lexers | VJ-009, VJ-010, VJ-053, VJ-054 |
| VJ-012 | P2 | implementation-with-proofs | Implement bounded exact number-token lexer | VJ-009, VJ-010, VJ-053, VJ-054 |
| VJ-013 | P2 | implementation-with-proofs | Build one scalar-and-container vertical slice | VJ-011, VJ-012, VJ-053, VJ-054 |
| VJ-014 | P2 | implementation-with-proofs | Implement scalar neutral codec prototype | VJ-007, VJ-013, VJ-053, VJ-054 |
| VJ-015 | P2 | maintainer-contract-release-infrastructure | Prepare bounded subprocess oracle transport prototype | VJ-002, VJ-007, VJ-013, VJ-014 |
| VJ-016 | P2 | maintainer-contract-release-infrastructure | Prepare one isolated serde_json smoke adapter | VJ-002, VJ-007, VJ-015 |
| VJ-017 | P3 | implementation-with-proofs | Implement UTF-8 decoding to wire units with soundness | VJ-009, VJ-010, VJ-005, VJ-053, VJ-054 |
| VJ-018 | P3 | proof-only | Prove UTF-8 decoder completeness | VJ-017, VJ-053, VJ-054 |
| VJ-019 | P3 | implementation-with-proofs | Implement string escape decoding and preservation | VJ-011, VJ-017, VJ-018, VJ-053, VJ-054 |
| VJ-020 | P3 | implementation-with-proofs | Implement strict scalar pairing validation | VJ-006, VJ-019, VJ-053, VJ-054 |
| VJ-021 | P3 | proof-only | Prove arbitrary-input number grammar equivalence | VJ-012, VJ-053, VJ-054 |
| VJ-022 | P3 | implementation-with-proofs | Implement array combinator and structural invariant | VJ-011, VJ-019, VJ-021, VJ-053, VJ-054 |
| VJ-023 | P3 | implementation-with-proofs | Implement object-member combinator and sequence invariant | VJ-011, VJ-019, VJ-021, VJ-053, VJ-054 |
| VJ-024 | P3 | proof-only | Compose full document parsing soundness | VJ-026, VJ-018, VJ-019, VJ-021, VJ-022, VJ-023, VJ-053, VJ-054 |
| VJ-025 | P3 | proof-only | Compose parsing completeness within profiles and budgets | VJ-024, VJ-027, VJ-028, VJ-053, VJ-054 |
| VJ-026 | P3 | implementation-with-proofs | Implement recursive document driver and termination | VJ-011, VJ-012, VJ-018, VJ-019, VJ-022, VJ-023, VJ-053, VJ-054 |
| VJ-027 | P3 | proof-only | Prove modeled parser and returned-AST resource bounds | VJ-026, VJ-006, VJ-053, VJ-054 |
| VJ-028 | P3 | implementation-with-proofs | Implement duplicate-key and full profile validation | VJ-020, VJ-023, VJ-006, VJ-053, VJ-054 |
| VJ-029 | P3 | implementation-with-proofs | Implement serializer and valid-output theorem | VJ-019, VJ-021, VJ-028, VJ-053, VJ-054 |
| VJ-030 | P3 | proof-only | Prove semantic serialization round trip | VJ-025, VJ-027, VJ-029, VJ-053, VJ-054 |
| VJ-031 | P3 | implementation-with-proofs | Complete neutral codec and preservation theorem | VJ-007, VJ-014, VJ-028, VJ-053, VJ-054 |
| VJ-032 | P3 | implementation-with-proofs | Bind public oracle entry points to reviewed claims | VJ-024, VJ-025, VJ-027, VJ-028, VJ-030, VJ-031, VJ-015, VJ-053, VJ-054 |
| VJ-033 | P3 | tests-docs | Classify public corpus and wire-profile regressions | VJ-024, VJ-025, VJ-028, VJ-031, VJ-032 |
| VJ-034 | P4 | maintainer-contract-release-infrastructure | Admit the minimum FloatLib proof closure | VJ-002, VJ-006, VJ-008 |
| VJ-035 | P4 | implementation-with-proofs | Implement exact-token decimal bridge with zero/range policy | VJ-021, VJ-034, VJ-053, VJ-054 |
| VJ-036 | P4 | proof-only | Prove arbitrary-decimal binary64 rounding capstone | VJ-035, VJ-034, VJ-053, VJ-054 |
| VJ-037 | P4 | implementation-with-proofs | Implement finite binary64 JSON serialization contract | VJ-029, VJ-036, VJ-053, VJ-054 |
| VJ-038 | P5 | maintainer-contract-release-infrastructure | Complete feature-isolated Rust adapter profile matrix | VJ-016, VJ-031, VJ-032 |
| VJ-039 | P5 | maintainer-contract-release-infrastructure | Implement profiled differential runner and classifier with seeded tests | VJ-033, VJ-038 |
| VJ-040 | P5 | maintainer-contract-release-infrastructure | Implement bounded discrepancy-preserving shrinker | VJ-039 |
| VJ-041 | P5 | tests-docs | Prepare regression and local repair/report drafts | VJ-040, VJ-038 |
| VJ-042 | P6 | tests-docs | Add adversarial mutations for proof and release gates | VJ-004, VJ-008, VJ-032 |
| VJ-043 | P6 | maintainer-contract-release-infrastructure | Rehearse one Linux source/CLI alpha package | VJ-032, VJ-033, VJ-038, VJ-040, VJ-041, VJ-042 |
| VJ-044 | P7 | implementation-with-proofs | Implement pure approved-result cache model and theorem | VJ-006, VJ-031, VJ-032, VJ-053, VJ-054 |
| VJ-045 | P7 | maintainer-contract-release-infrastructure | Prepare bounded checked-runtime cache implementation pilot | VJ-044, VJ-038, VJ-043 |
| VJ-046 | P7 | tests-docs | Benchmark unique-input checked workloads and limits | VJ-045 |
| VJ-047 | P8 | maintainer-contract-release-infrastructure | Prepare offline feedback and approved reporter qualification | VJ-041, VJ-045, VJ-046 |
| VJ-048 | P9 | implementation-with-proofs | Qualify one safe-Rust fast path via extraction and refinement | VJ-032, VJ-038, VJ-045, VJ-053, VJ-054 |
| VJ-049 | P10 | maintainer-contract-release-infrastructure | Prepare official Lean upgrade and stable qualification candidate | VJ-002, VJ-042, VJ-043 |
| VJ-050 | P10 | maintainer-contract-release-infrastructure | Freeze downstream compatibility and stable release checklist | VJ-043, VJ-049 |
| VJ-051 | P1 | maintainer-contract-release-infrastructure | Qualify a minimum current-Lean comparator and replay envelope | VJ-004, VJ-054 |
| VJ-052 | P1 | maintainer-contract-release-infrastructure | Implement the bounded submission supervisor adapter | VJ-051, VJ-008 |
| VJ-053 | P1 | maintainer-contract-release-infrastructure | Qualify the operational mathematical submission gate | VJ-052, VJ-051 |
| VJ-054 | P0 | maintainer-contract-release-infrastructure | Prepare the Lean and Rust workspace skeleton | VJ-001, VJ-002 |
| VJ-055 | P4 | implementation-with-proofs | Bind binary64 operations into the public oracle and transport | VJ-036, VJ-037, VJ-032, VJ-031, VJ-053, VJ-054 |

## Individual work packets

### VJ-001 Select project ownership, names and provenance policy

Class: `maintainer-contract-release-infrastructure`. Phase: P0. Prerequisites: none.

Prepare one reviewable bootstrap decision; no hosting or registry writes.

Allowed files and artifacts: `docs/OWNERSHIP.md`, `docs/PROVENANCE.md`, `LICENSE`, `NOTICE`.

Acceptance criteria:

- Repository/crate name checks and designated contract/release maintainers are recorded as dated evidence.
- Fresh source licensing and third-party reuse rules are explicit; private records and operational data are excluded.
- Bootstrap and publication are distinct actions with no automatic execution.

Human review: Operator ownership decision and independent license/provenance review.

Intended capstones: none. Required gates: G00, G02, G05, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-001.json).

### VJ-002 Freeze stable and development Lean lane candidates

Class: `maintainer-contract-release-infrastructure`. Phase: P0. Prerequisites: VJ-001.

Qualify exact current stable and RC/dependency candidates without changing the governed corpus.

Allowed files and artifacts: `lean-toolchain`, `lake-manifest.json`, `docs/TOOLCHAINS.md`, `compatibility/toolchains.json`.

Acceptance criteria:

- Official release identities and artifact hashes are recorded; each execution pin is immutable.
- Effective compiler after dependency resolution equals the selected lane; caches are isolated by complete closure.
- If no newer RC exists, stable development fallback is explicit; failed checker/dependency compatibility remains an infrastructure blocker.

Human review: Toolchain/dependency admission review; no automatic downgrade.

Intended capstones: none. Required gates: G00, G02, G05, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-002.json).

### VJ-003 Prepare native GitHub six-hour courtesy reservations

Class: `maintainer-contract-release-infrastructure`. Phase: P0. Prerequisites: VJ-001.

Use native Issues, sub-issues, dependencies, comments, assignees and Projects; no bot or custom tracker.

Allowed files and artifacts: `docs/CLAIM-WORKFLOW.md`.

Acceptance criteria:

- One issue points to one immutable packet revision; native blocked-by and phase parent relationships mirror its prerequisite IDs.
- Contributor comments with packet identity and proposed six-hour interval; maintainer acknowledges/assigns and records UTC start/expiry in the issue or Projects field.
- Expiry, cancellation and reassignment are manual coordination actions; stale reservations never authorize merge or change the frozen contract.

Human review: Maintainer qualification of repository permissions, manual reservation/reassignment procedure and readiness gate.

Intended capstones: none. Required gates: G00, G02, G05, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-003.json).

### VJ-004 Prepare frozen-packet and Lean acceptance gate contract

Class: `maintainer-contract-release-infrastructure`. Phase: P1. Prerequisites: VJ-002.

Define one small future tools/verify-ticket entry point and reuse qualified Lean checkers; no claim database or new product.

Allowed files and artifacts: `docs/WORK-PACKETS.md`, `docs/LEAN-GATES.md`, `tools/verify-ticket`.

Acceptance criteria:

- Packet schema requires exact source, theorem types, definition/instance closure, bindings and command identities before readiness.
- Validator plan refuses changed meaning, files outside allowlist, missing dependencies, custom axioms and unsupported native substitution claims.
- Existing declaration-index and kernel replay facilities are inventoried before any bespoke checking code is proposed.
- This defines the contract only: VJ-051/VJ-052/VJ-053 separately implement and qualify the operational gate before mathematical claims.

Human review: Independent reviewer of checker policy and executable gate definitions.

Intended capstones: none. Required gates: G00, G02, G05, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-004.json).

### VJ-005 Review wire AST and independent JSON relations

Class: `maintainer-contract-release-infrastructure`. Phase: P1. Prerequisites: VJ-001, VJ-002.

Draft and independently review wire UTF-16 units, ordered members, number tokens and complete-document grammar.

Allowed files and artifacts: `lean/VerifiedJson/Spec/Wire.lean`, `lean/VerifiedJson/Spec/Grammar.lean`, `docs/SPEC-WIRE.md`.

Acceptance criteria:

- Wire AST preserves duplicates and number lexemes without claiming whitespace/escape-spelling reconstruction.
- Escaped unpaired surrogates are representable; unescaped UTF-8 and permitted whitespace follow independent grammar relations.
- Constructive accepted/rejected examples establish nonvacuity; relations never depend on parser success.

Human review: Two semantic reviewers; explicit RFC/profile policy decisions.

Intended capstones: J02, J03, J04, J05, J06. Required gates: G00, G02, G05, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-005.json).

### VJ-006 Review budgets, results, profiles and public API predicates

Class: `maintainer-contract-release-infrastructure`. Phase: P1. Prerequisites: VJ-005.

Freeze result categories and scope sufficient to state all core and later runtime theorems.

Allowed files and artifacts: `lean/VerifiedJson/Spec/Profiles.lean`, `lean/VerifiedJson/Spec/Budgets.lean`, `lean/VerifiedJson/Spec/PublicApi.lean`, `docs/SPEC-PROFILES.md`.

Acceptance criteria:

- Accepted, InvalidSyntax, ProfileRejected, LimitExceeded, Unsupported and InfrastructureFailure have disjoint documented meanings.
- WellFormed AST and budget sufficiency are defined independently of parser/serializer completion.
- Scalar/duplicate/number policies, signed-zero/range decisions and returned-result resource operations are explicit; concrete defaults need human selection.

Human review: Semantic and security review of defaults, rejection reasons and resource-model limits.

Intended capstones: J07, J08, J09, J10, J11, J12, J13, J15, J16. Required gates: G00, G02, G05, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-006.json).

### VJ-007 Review independent neutral transport and comparison contract

Class: `maintainer-contract-release-infrastructure`. Phase: P1. Prerequisites: VJ-005, VJ-006.

Freeze a bounded non-JSON codec and candidate-specific equality projections.

Allowed files and artifacts: `lean/VerifiedJson/Spec/Protocol.lean`, `lean/VerifiedJson/Spec/Comparison.lean`, `docs/PROTOCOL.md`.

Acceptance criteria:

- Protocol directly represents wire units, ordered duplicate members, exact tokens, numerical bits and result classes.
- Length framing and decode limits are explicit; candidate JSON parsing cannot serve as its own oracle transport.
- Comparison domains distinguish grammar, profile, numeric, limit and infrastructure disagreements.

Human review: Independent protocol/adapter preservation review.

Intended capstones: J14, J17. Required gates: G00, G02, G05, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-007.json).

### VJ-008 Create claim-root ledger and concrete packet sealing procedure

Class: `maintainer-contract-release-infrastructure`. Phase: P1. Prerequisites: VJ-004, VJ-005, VJ-006, VJ-007.

Bind intended J01–J17 obligations to actual elaborated declarations only when those declarations exist.

Allowed files and artifacts: `lean/VerifiedJson/Claims.lean`, `docs/CLAIMS.md`, `docs/claim-roots.json`, `work-packets/`.

Acceptance criteria:

- Unbuilt roots are marked missing rather than synthesized as passed; public API and codec roots remain explicit.
- Sealing fills exact target/source/type/meaning/binding/validator pins and scoped proof-body selectors before a ticket becomes claimable.
- Dependencies refer to merged accepted commits, not proposed PRs; each six-hour scope is rehearsed or split before opening.
- Manual/bootstrap packets may use approved review checklists; mathematical packets require the operational VJ-053 envelope.

Human review: Maintainer semantic owner approves every sealed root and packet.

Intended capstones: J01, J02, J03, J04, J05, J06, J07, J08, J09, J10, J11, J12, J13, J14, J15, J16, J17. Required gates: G00, G02, G05, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-008.json).

### VJ-009 Implement bounded byte cursor read primitives

Class: `implementation-with-proofs`. Phase: P2. Prerequisites: VJ-005, VJ-006, VJ-008, VJ-053, VJ-054.

Implement one cursor module and prove read bounds against its frozen relation.

Allowed files and artifacts: `lean/VerifiedJson/Impl/Cursor.lean`, `lean/VerifiedJson/Proofs/CursorRead.lean`.

Acceptance criteria:

- Read at end returns the specified outcome; successful reads return the input byte at a proved valid index.
- Empty input and last-byte fixtures pass; cursor/result representation changes are excluded.
- Implementation bodies may change only within the sealed Cursor module; target statements and definitions in Spec remain frozen.

Human review: Independent maintainer review of contract preservation and submitted evidence.

Intended capstones: J01. Required gates: G00, G01, G02, G03, G04, G05, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-009.json).

### VJ-010 Prove cursor advance and checked-length arithmetic bounds

Class: `proof-only`. Phase: P2. Prerequisites: VJ-009, VJ-053, VJ-054.

Discharge only frozen advance/addition/progress obligations in the accepted primitive implementation.

Allowed files and artifacts: `lean/VerifiedJson/Proofs/CursorAdvance.lean`.

Acceptance criteria:

- Advance cannot exceed input or wrap an arithmetic boundary.
- Progress and failure cases match the independent operation relation.
- No implementation, statement, instance-resolution or profile change is accepted as a proof repair.

Human review: Independent maintainer review of contract preservation and submitted evidence.

Intended capstones: J01, J08. Required gates: G00, G01, G02, G03, G04, G05, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-010.json).

### VJ-011 Implement whitespace and fixed literal lexers

Class: `implementation-with-proofs`. Phase: P2. Prerequisites: VJ-009, VJ-010, VJ-053, VJ-054.

Add only whitespace/null/true/false token primitives.

Allowed files and artifacts: `lean/VerifiedJson/Impl/Literals.lean`, `lean/VerifiedJson/Proofs/Literals.lean`.

Acceptance criteria:

- Successful tokens match independent literal/whitespace relations with consumed-index bounds.
- Truncation, suffixes and forbidden whitespace fixtures retain documented outcomes.
- Each loop's progress/remaining-input measure is proved; trailing-document policy is left to the document wrapper.

Human review: Independent maintainer review of contract preservation and submitted evidence.

Intended capstones: J05, J07. Required gates: G00, G01, G02, G03, G04, G05, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-011.json).

### VJ-012 Implement bounded exact number-token lexer

Class: `implementation-with-proofs`. Phase: P2. Prerequisites: VJ-009, VJ-010, VJ-053, VJ-054.

Produce original number tokens with local progress and budget proofs; numerical conversion is separate.

Allowed files and artifacts: `lean/VerifiedJson/Impl/NumberLexer.lean`, `lean/VerifiedJson/Proofs/NumberLexerLocal.lean`.

Acceptance criteria:

- Token spelling is preserved and exponent/digit work is bounded by the reviewed limits.
- Leading zeros, missing fraction/exponent digits, signs and delimiter boundaries have fixtures.
- No floating-point conversion or normalization changes grammar acceptance.

Human review: Independent maintainer review of contract preservation and submitted evidence.

Intended capstones: J04, J07, J08. Required gates: G00, G01, G02, G03, G04, G05, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-012.json).

### VJ-013 Build one scalar-and-container vertical slice

Class: `implementation-with-proofs`. Phase: P2. Prerequisites: VJ-011, VJ-012, VJ-053, VJ-054.

Compose literal/number tokens and one shallow array/object slice through frozen parser interfaces.

Allowed files and artifacts: `lean/VerifiedJson/Impl/VerticalSlice.lean`, `lean/VerifiedJson/Proofs/VerticalSlice.lean`.

Acceptance criteria:

- Only the declared bounded slice is claimed; strings/deeper cases return Unsupported or use separately specified interfaces.
- Positive and rejection paths bind to independent slice relations.
- One interface/driver abstraction is ready for later combinators without treating slice success as full JSON completeness.

Human review: Independent maintainer review of contract preservation and submitted evidence.

Intended capstones: J05, J07, J08. Required gates: G00, G01, G02, G03, G04, G05, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-013.json).

### VJ-014 Implement scalar neutral codec prototype

Class: `implementation-with-proofs`. Phase: P2. Prerequisites: VJ-007, VJ-013, VJ-053, VJ-054.

Encode/decode the vertical-slice outcomes with length-delimited frames.

Allowed files and artifacts: `lean/VerifiedJson/Impl/ProtocolScalar.lean`, `lean/VerifiedJson/Proofs/ProtocolScalar.lean`.

Acceptance criteria:

- Scalar token/result round trips are proved within explicit frame limits.
- Malformed lengths, truncation and wrong versions are distinct transport outcomes.
- Codec never invokes the Rust candidate parser; exact wire unit/bit distinctions are retained.

Human review: Independent maintainer review of contract preservation and submitted evidence.

Intended capstones: J17. Required gates: G00, G01, G02, G03, G04, G05, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-014.json).

### VJ-015 Prepare bounded subprocess oracle transport prototype

Class: `maintainer-contract-release-infrastructure`. Phase: P2. Prerequisites: VJ-002, VJ-007, VJ-013, VJ-014.

Implement and test one pinned-executable subprocess boundary as explicitly trusted/tested infrastructure.

Allowed files and artifacts: `crates/json-oracle/`, `docs/ORACLE-TRANSPORT.md`, `tests/transport/prototype/`.

Acceptance criteria:

- Separate diagnostics and length-bounded frames survive chunking/truncation tests.
- Missing readiness, timeout and worker death are InfrastructureFailure; partial output cannot approve a result.
- Executable/target/protocol identities are checked and no hidden tool download occurs.

Human review: Independent native transport/termination/resource-boundary review; no Rust proof claim.

Intended capstones: J16, J17. Required gates: G00, G02, G05, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-015.json).

### VJ-016 Prepare one isolated serde_json smoke adapter

Class: `maintainer-contract-release-infrastructure`. Phase: P2. Prerequisites: VJ-002, VJ-007, VJ-015.

Build one exact Rust API/feature cell for a reproducible synthetic discrepancy.

Allowed files and artifacts: `crates/json-adapter-serde/`, `compatibility/serde-smoke.json`, `tests/adapters/smoke/`.

Acceptance criteria:

- Target source/checksum, lock, Rust target and effective feature set are observed, not inferred from requested features.
- Smoke scope identifies where Value/visitor conversion loses distinctions; it never claims complete lossless equivalence.
- A deliberately seeded mismatch is reproducible with pinned outcomes and input; no upstream bug is fabricated.

Human review: Adapter/numerical policy review.

Intended capstones: J14. Required gates: G00, G02, G05, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-016.json).

### VJ-017 Implement UTF-8 decoding to wire units with soundness

Class: `implementation-with-proofs`. Phase: P3. Prerequisites: VJ-009, VJ-010, VJ-005, VJ-053, VJ-054.

Decode valid raw scalars and encode them into UTF-16 units.

Allowed files and artifacts: `lean/VerifiedJson/Impl/Utf8.lean`, `lean/VerifiedJson/Proofs/Utf8Sound.lean`.

Acceptance criteria:

- Successful decodes satisfy the frozen scalar/UTF-16 relation.
- Overlong forms, continuation errors, surrogate encodings and out-of-range scalars are rejected appropriately.
- Input progress, output-unit bounds and maximum scalar encoding cases are covered.

Human review: Independent maintainer review of contract preservation and submitted evidence.

Intended capstones: J02. Required gates: G00, G01, G02, G03, G04, G05, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-017.json).

### VJ-018 Prove UTF-8 decoder completeness

Class: `proof-only`. Phase: P3. Prerequisites: VJ-017, VJ-053, VJ-054.

Prove every admitted raw scalar encoding reaches its expected units under sufficient declared limits.

Allowed files and artifacts: `lean/VerifiedJson/Proofs/Utf8Complete.lean`.

Acceptance criteria:

- Completeness premise is independent valid encoding plus budget sufficiency, never decoder success.
- One-through-four-byte positive witnesses and malformed rejection witnesses are retained.
- Frozen decoder and semantic closure are unchanged.

Human review: Independent maintainer review of contract preservation and submitted evidence.

Intended capstones: J02. Required gates: G00, G01, G02, G03, G04, G05, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-018.json).

### VJ-019 Implement string escape decoding and preservation

Class: `implementation-with-proofs`. Phase: P3. Prerequisites: VJ-011, VJ-017, VJ-018, VJ-053, VJ-054.

Add string termination, simple escapes and four-hex-unit escapes against the wire relation.

Allowed files and artifacts: `lean/VerifiedJson/Impl/StringLexer.lean`, `lean/VerifiedJson/Proofs/Escapes.lean`.

Acceptance criteria:

- Each escaped code unit is preserved, including lone surrogates.
- Equivalent raw/escaped supplementary characters give equal wire units; invalid hex/truncated escape/control-byte cases are specified.
- Consumed-input, decoded-output and work bounds hold; no Unicode normalization occurs.

Human review: Independent maintainer review of contract preservation and submitted evidence.

Intended capstones: J03, J07, J08. Required gates: G00, G01, G02, G03, G04, G05, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-019.json).

### VJ-020 Implement strict scalar pairing validation

Class: `implementation-with-proofs`. Phase: P3. Prerequisites: VJ-006, VJ-019, VJ-053, VJ-054.

Validate wire units against the independently reviewed scalar-profile predicate.

Allowed files and artifacts: `lean/VerifiedJson/Impl/ScalarProfile.lean`, `lean/VerifiedJson/Proofs/ScalarProfile.lean`.

Acceptance criteria:

- Successful and rejected validation outcomes are proved against surrogate pairing.
- Raw/escaped supplementary forms agree; lone high/low surrogates remain valid wire data but fail the selected scalar profile.
- Key spelling/normalization is unchanged; bounds include deeply nested profile traversal only where the sealed scope covers it.

Human review: Independent maintainer review of contract preservation and submitted evidence.

Intended capstones: J11. Required gates: G00, G01, G02, G03, G04, G05, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-020.json).

### VJ-021 Prove arbitrary-input number grammar equivalence

Class: `proof-only`. Phase: P3. Prerequisites: VJ-012, VJ-053, VJ-054.

Compose soundness/completeness for the frozen number lexer with exact token boundaries.

Allowed files and artifacts: `lean/VerifiedJson/Proofs/NumberLexerComplete.lean`.

Acceptance criteria:

- Accepted lexemes satisfy the grammar and every admitted lexeme within limits is accepted.
- Malformed numeric forms are not hidden behind parser-success premises.
- Suffix/consumed-index results distinguish lexing from complete-document validation.

Human review: Independent maintainer review of contract preservation and submitted evidence.

Intended capstones: J04. Required gates: G00, G01, G02, G03, G04, G05, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-021.json).

### VJ-022 Implement array combinator and structural invariant

Class: `implementation-with-proofs`. Phase: P3. Prerequisites: VJ-011, VJ-019, VJ-021, VJ-053, VJ-054.

Build one parameterized element-parser combinator with frozen element correctness assumptions.

Allowed files and artifacts: `lean/VerifiedJson/Impl/Arrays.lean`, `lean/VerifiedJson/Proofs/Arrays.lean`.

Acceptance criteria:

- Array result sequence and delimiters satisfy the independent relation when the supplied element contract holds.
- Separator/trailing-comma/truncation fixtures and local progress/cost obligations pass.
- The assumption cannot be satisfied by a circular self-proof; recursion is discharged in the separate driver ticket.

Human review: Independent maintainer review of contract preservation and submitted evidence.

Intended capstones: J05, J07, J08. Required gates: G00, G01, G02, G03, G04, G05, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-022.json).

### VJ-023 Implement object-member combinator and sequence invariant

Class: `implementation-with-proofs`. Phase: P3. Prerequisites: VJ-011, VJ-019, VJ-021, VJ-053, VJ-054.

Build the object combinator using ordered member sequences and a parameterized value parser.

Allowed files and artifacts: `lean/VerifiedJson/Impl/Objects.lean`, `lean/VerifiedJson/Proofs/Objects.lean`.

Acceptance criteria:

- Members and duplicate keys remain in source order after decoded-key parsing.
- Colon/separator/trailing-comma/truncation tests and local bounds pass.
- No intermediate map silently collapses duplicates; recursion assumptions are discharged by the driver.

Human review: Independent maintainer review of contract preservation and submitted evidence.

Intended capstones: J05, J07, J08. Required gates: G00, G01, G02, G03, G04, G05, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-023.json).

### VJ-024 Compose full document parsing soundness

Class: `proof-only`. Phase: P3. Prerequisites: VJ-026, VJ-018, VJ-019, VJ-021, VJ-022, VJ-023, VJ-053, VJ-054.

Discharge the frozen Accepted-implies-independent-document-relation root by module composition.

Allowed files and artifacts: `lean/VerifiedJson/Proofs/ParseSound.lean`.

Acceptance criteria:

- All constructors and complete-document consumption are covered.
- Trailing non-whitespace and bad nested tokens cannot be accepted.
- Top-level theorem type, parser body and relation closure match the frozen packet; helper lemmas cannot redefine acceptance.

Human review: Independent maintainer review of contract preservation and submitted evidence.

Intended capstones: J05. Required gates: G00, G01, G02, G03, G04, G05, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-024.json).

### VJ-025 Compose parsing completeness within profiles and budgets

Class: `proof-only`. Phase: P3. Prerequisites: VJ-024, VJ-027, VJ-028, VJ-053, VJ-054.

Prove complete coverage from independent document/profile and sufficient-budget premises.

Allowed files and artifacts: `lean/VerifiedJson/Proofs/ParseComplete.lean`.

Acceptance criteria:

- Every constructor has a constructive witness with derived budgets.
- Parser success and serializer-produced-only inputs are not completeness premises.
- Syntax/profile/limit outcomes remain distinct; full grammar and strict scalar profiles have explicit separate scopes.

Human review: Independent maintainer review of contract preservation and submitted evidence.

Intended capstones: J06. Required gates: G00, G01, G02, G03, G04, G05, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-025.json).

### VJ-026 Implement recursive document driver and termination

Class: `implementation-with-proofs`. Phase: P3. Prerequisites: VJ-011, VJ-012, VJ-018, VJ-019, VJ-022, VJ-023, VJ-053, VJ-054.

Connect the fixed primitives and combinators with well-founded recursion and one-document consumption.

Allowed files and artifacts: `lean/VerifiedJson/Impl/Parser.lean`, `lean/VerifiedJson/Proofs/ParseTermination.lean`.

Acceptance criteria:

- Every byte input terminates in a reviewed result; no opaque/unreviewed fuel assumption remains.
- Recursion measure decreases and combinator hypotheses are discharged without circular imports.
- Input/depth/work refusals are explicit; termination theorem does not claim native stack safety.

Human review: Independent maintainer review of contract preservation and submitted evidence.

Intended capstones: J07, J05. Required gates: G00, G01, G02, G03, G04, G05, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-026.json).

### VJ-027 Prove modeled parser and returned-AST resource bounds

Class: `proof-only`. Phase: P3. Prerequisites: VJ-026, VJ-006, VJ-053, VJ-054.

Discharge frozen cost/allocation/length bounds for the selected core profile.

Allowed files and artifacts: `lean/VerifiedJson/Proofs/ParseResources.lean`.

Acceptance criteria:

- The counted operation model and its native limitations are stated, including output nodes/units/tokens and arithmetic.
- Empty, invalid, deeply nested and huge numeric inputs satisfy bound/refusal statements.
- No resource failure is reclassified as invalid syntax; traversal/encoding/destruction exclusions are named until independently qualified.

Human review: Independent maintainer review of contract preservation and submitted evidence.

Intended capstones: J08. Required gates: G00, G01, G02, G03, G04, G05, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-027.json).

### VJ-028 Implement duplicate-key and full profile validation

Class: `implementation-with-proofs`. Phase: P3. Prerequisites: VJ-020, VJ-023, VJ-006, VJ-053, VJ-054.

Implement the selected decoded-key duplicate policy and bounded AST profile traversal.

Allowed files and artifacts: `lean/VerifiedJson/Impl/Profiles.lean`, `lean/VerifiedJson/Proofs/Profiles.lean`.

Acceptance criteria:

- Escape-equivalent keys are compared as decoded wire/scalar units according to the frozen profile.
- Allow/reject policy outcomes are proved; normalization/case-folding is absent.
- ProfileRejected and LimitExceeded are distinguished and traversal budgets are explicit.

Human review: Independent maintainer review of contract preservation and submitted evidence.

Intended capstones: J11. Required gates: G00, G01, G02, G03, G04, G05, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-028.json).

### VJ-029 Implement serializer and valid-output theorem

Class: `implementation-with-proofs`. Phase: P3. Prerequisites: VJ-019, VJ-021, VJ-028, VJ-053, VJ-054.

Serialize independently WellFormed ASTs without restricting the domain to prior parse output.

Allowed files and artifacts: `lean/VerifiedJson/Impl/Serializer.lean`, `lean/VerifiedJson/Proofs/SerializeValid.lean`.

Acceptance criteria:

- Every successful output meets document/profile grammar with explicit output/work budgets.
- Escaped units, duplicate sequence and original number-token policy are preserved.
- Output exhaustion returns a limit outcome; success never contains a truncated document.

Human review: Independent maintainer review of contract preservation and submitted evidence.

Intended capstones: J09. Required gates: G00, G01, G02, G03, G04, G05, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-029.json).

### VJ-030 Prove semantic serialization round trip

Class: `proof-only`. Phase: P3. Prerequisites: VJ-025, VJ-027, VJ-029, VJ-053, VJ-054.

Compose serializer/parser properties with sufficient parsing budgets derived from generated output.

Allowed files and artifacts: `lean/VerifiedJson/Proofs/SerializeRoundtrip.lean`.

Acceptance criteria:

- Independent WellFormed AST is the input predicate and semantic equality preserves members/units/tokens.
- Escape expansion and nested-depth bounds yield the documented parsing budget.
- Byte-for-byte reconstruction is not claimed without source spans/bytes; parsing-success premises are excluded.

Human review: Independent maintainer review of contract preservation and submitted evidence.

Intended capstones: J10. Required gates: G00, G01, G02, G03, G04, G05, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-030.json).

### VJ-031 Complete neutral codec and preservation theorem

Class: `implementation-with-proofs`. Phase: P3. Prerequisites: VJ-007, VJ-014, VJ-028, VJ-053, VJ-054.

Extend the codec to every AST/outcome variant and prove bounded decoding and round trips.

Allowed files and artifacts: `lean/VerifiedJson/Impl/Protocol.lean`, `lean/VerifiedJson/Proofs/Protocol.lean`, `tests/transport/full/`.

Acceptance criteria:

- Lone units, duplicate sequences, exact tokens and exact binary bit fields survive transport.
- Truncated/oversized/deep frames fail in the declared transport category.
- Comparator/decoder work and native deep-result boundary fixtures are included; no Rust String/map narrowing occurs.

Human review: Independent maintainer review of contract preservation and submitted evidence.

Intended capstones: J17. Required gates: G00, G01, G02, G03, G04, G05, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-031.json).

### VJ-032 Bind public oracle entry points to reviewed claims

Class: `implementation-with-proofs`. Phase: P3. Prerequisites: VJ-024, VJ-025, VJ-027, VJ-028, VJ-030, VJ-031, VJ-015, VJ-053, VJ-054.

Implement and prove one exported oracle dispatch layer while documenting concrete transport/compiler assumptions.

Allowed files and artifacts: `lean/VerifiedJson/Impl/OracleApi.lean`, `lean/VerifiedJson/Proofs/OracleApi.lean`, `docs/API-BINDINGS.md`.

Acceptance criteria:

- Every exported operation maps to frozen parser/profile/serializer roots and exact result predicates.
- No export silently chooses a weaker profile or mode; limits and infrastructure failures retain their meanings.
- Compiled artifact/protocol bindings are explicit evidence, not a machine-code proof inferred from Lean source.

Human review: Independent maintainer review of contract preservation and submitted evidence.

Intended capstones: J16. Required gates: G00, G01, G02, G03, G04, G05, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-032.json).

### VJ-033 Classify public corpus and wire-profile regressions

Class: `tests-docs`. Phase: P3. Prerequisites: VJ-024, VJ-025, VJ-028, VJ-031, VJ-032.

Pin licensed corpus sources and add bounded fixtures for policy-sensitive cases.

Allowed files and artifacts: `tests/corpus/`, `tests/regressions/wire/`, `docs/CORPUS.md`.

Acceptance criteria:

- JSONTestSuite accepted/rejected/implementation-dependent labels are preserved.
- Every fixture has profile/limit identity and expected category; surrogates/duplicate escaped keys/trailing bytes are represented.
- Corpus observations complement proofs and do not substitute for missing roots; copied fixture notices are retained.

Human review: Fixture provenance and expected-policy review.

Intended capstones: none. Required gates: G00, G02, G05, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-033.json).

### VJ-034 Admit the minimum FloatLib proof closure

Class: `maintainer-contract-release-infrastructure`. Phase: P4. Prerequisites: VJ-002, VJ-006, VJ-008.

Inspect, build and replay one exact minimal FloatLib module closure, with patches only if reviewed.

Allowed files and artifacts: `lean/VerifiedJson/Numbers/Provider.lean`, `compatibility/float-provider.json`, `docs/FLOAT-ADMISSION.md`.

Acceptance criteria:

- Arbitrary decimal parse coverage is inspected separately from finite-format round-trip claims.
- Exact source/patch/license/import/axiom/native closure and stable/RC compatibility are recorded.
- Effective toolchain remains selected; statement/definition-altering dependency changes require semantic review.

Human review: Numerical semantic review and dependency admission; no automatic upstream posting.

Intended capstones: J12, J13. Required gates: G00, G02, G05, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-034.json).

### VJ-035 Implement exact-token decimal bridge with zero/range policy

Class: `implementation-with-proofs`. Phase: P4. Prerequisites: VJ-021, VJ-034, VJ-053, VJ-054.

Connect admitted JSON tokens to exact signed decimals and the one destination rounding operation.

Allowed files and artifacts: `lean/VerifiedJson/Numbers/DecimalBridge.lean`, `lean/VerifiedJson/Proofs/DecimalBridge.lean`.

Acceptance criteria:

- No intermediate fixed-decimal rounding is introduced.
- Sign of zero, supported exponent/digit budgets and range outcomes match the frozen profile.
- Local interpretation/progress proofs hold for arbitrary supported tokens, including extreme-exponent refusal cases.

Human review: Independent maintainer review of contract preservation and submitted evidence.

Intended capstones: J12. Required gates: G00, G01, G02, G03, G04, G05, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-035.json).

### VJ-036 Prove arbitrary-decimal binary64 rounding capstone

Class: `proof-only`. Phase: P4. Prerequisites: VJ-035, VJ-034, VJ-053, VJ-054.

Compose provider and token interpretation proofs into correctly rounded binary64 conversion.

Allowed files and artifacts: `lean/VerifiedJson/Proofs/Binary64Round.lean`.

Acceptance criteria:

- Nearest-even ties, subnormals, signed zero, underflow and overflow satisfy explicit bit/status statements.
- The theorem quantifies over arbitrary supported tokens rather than only formatted finite values.
- Required native bit/bridge assumptions are named; missing provider coverage remains a blocker.

Human review: Independent maintainer review of contract preservation and submitted evidence.

Intended capstones: J12. Required gates: G00, G01, G02, G03, G04, G05, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-036.json).

### VJ-037 Implement finite binary64 JSON serialization contract

Class: `implementation-with-proofs`. Phase: P4. Prerequisites: VJ-029, VJ-036, VJ-053, VJ-054.

Produce valid chosen decimal text for finite values and prove its stated parse round trip.

Allowed files and artifacts: `lean/VerifiedJson/Numbers/FloatSerializer.lean`, `lean/VerifiedJson/Proofs/FloatSerializer.lean`.

Acceptance criteria:

- Signed zero and exact finite bit patterns round-trip under the reviewed parse profile.
- Nonfinite inputs and output/work exhaustion have explicit outcomes.
- Shortest formatting/JCS conformance is excluded unless separately reviewed and proved.

Human review: Independent maintainer review of contract preservation and submitted evidence.

Intended capstones: J13. Required gates: G00, G01, G02, G03, G04, G05, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-037.json).

### VJ-038 Complete feature-isolated Rust adapter profile matrix

Class: `maintainer-contract-release-infrastructure`. Phase: P5. Prerequisites: VJ-016, VJ-031, VJ-032.

Qualify explicit default/f64/exact/raw/order API cells without promising generic Serde verification.

Allowed files and artifacts: `crates/json-adapter-serde/`, `compatibility/serde-profiles/`, `tests/adapters/full/`.

Acceptance criteria:

- Effective Cargo feature unification is measured and incompatible cells are isolated.
- Custom visitor/RawValue/token observation paths are checked for duplicate/member/number preservation; lossy domains are excluded or explicitly projected.
- Default accuracy differences, declared round-trip guarantees, profile differences and genuine defects remain distinct.
- Only qualified cells are enabled: actual binary64 oracle comparisons additionally require VJ-036 and VJ-037; unavailable cells remain Unsupported, not passed.
- A binary64 cell additionally requires accepted VJ-055 public-API/compiled-oracle binding; proved number modules alone cannot enable it.

Human review: Adapter contract and numerical-classification review; tested/native boundary explicitly retained.

Intended capstones: J14. Required gates: G00, G02, G05, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-038.json).

### VJ-039 Implement profiled differential runner and classifier with seeded tests

Class: `maintainer-contract-release-infrastructure`. Phase: P5. Prerequisites: VJ-033, VJ-038.

Wire accepted adapters into a bounded local runner and contract-driven classifier, with synthetic generator/mutant fixtures.

Allowed files and artifacts: `crates/json-diff/src/run.rs`, `crates/json-diff/src/classify.rs`, `tests/generators/`, `tests/classifier/`, `tests/mutants/candidate/`.

Acceptance criteria:

- Grammar/semantic defects and allowed profile/accuracy/range differences have separate expected classes.
- Seeded candidate defects are detected; permitted disagreements do not become upstream bug claims.
- Every run records pinned inputs/build/profile/limit identities and no private data.
- Numeric-only cells without admitted provider evidence remain Unsupported; synthetic classifier fixtures are not claimed as real conversion evidence.

Human review: Classification semantics and native tool boundary review; no all-input candidate proof.

Intended capstones: none. Required gates: G00, G02, G05, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-039.json).

### VJ-040 Implement bounded discrepancy-preserving shrinker

Class: `maintainer-contract-release-infrastructure`. Phase: P5. Prerequisites: VJ-039.

Add AST and byte shrinking for one pinned failure class; avoid proving unimplemented global minimality.

Allowed files and artifacts: `crates/json-diff/src/shrink.rs`, `crates/json-diff/src/cli.rs`, `tests/shrinker/`.

Acceptance criteria:

- Every retained reduction reproduces the same classified discrepancy under fixed builds.
- Cancellation, reduction budget and candidate crashes preserve the original evidence and stop safely.
- A small irreducible test is called minimized, not globally minimal, unless that stronger property is established.

Human review: Infrastructure/counterexample review; no automatic upstream disclosure.

Intended capstones: none. Required gates: G00, G02, G05, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-040.json).

### VJ-041 Prepare regression and local repair/report drafts

Class: `tests-docs`. Phase: P5. Prerequisites: VJ-040, VJ-038.

Create synthetic maintainer-facing issue/patch templates and repair validation examples.

Allowed files and artifacts: `tests/repair-drafts/`, `docs/UPSTREAM-REPRODUCER.md`, `docs/REPAIR-BOUNDARY.md`.

Acceptance criteria:

- Draft includes minimized bytes, expected/observed outcomes, exact versions/features, reproducer and regression.
- A repair cannot change frozen contract, remove assertions, or auto-replace deployed binaries.
- Synthetic replay and target contribution checks are documented; external posting and real security disclosure are separate actions.

Human review: Expected behavior and disclosure/repair scope review.

Intended capstones: none. Required gates: G00, G02, G05, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-041.json).

### VJ-042 Add adversarial mutations for proof and release gates

Class: `tests-docs`. Phase: P6. Prerequisites: VJ-004, VJ-008, VJ-032.

Exercise existing gates against intentionally invalid candidate artifacts.

Allowed files and artifacts: `tests/mutants/proof-gates/`, `tests/mutants/release/`.

Acceptance criteria:

- Mutants include false/missing roots, custom axioms, changed definitions, stale artifacts, weak hypotheses and skipped checking.
- Each mutant fails the intended gate; checker-unavailable and failed-write cases are infrastructure rather than proof rejection.
- Unproved extern/implemented_by substitution and forged coverage/package manifests cannot obtain a stronger claim.

Human review: Independent gate-audit review of detection assertions.

Intended capstones: none. Required gates: G00, G02, G05, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-042.json).

### VJ-043 Rehearse one Linux source/CLI alpha package

Class: `maintainer-contract-release-infrastructure`. Phase: P6. Prerequisites: VJ-032, VJ-033, VJ-038, VJ-040, VJ-041, VJ-042.

Prepare an installable source/oracle/CLI candidate and inspect the packaged bytes; no release.

Allowed files and artifacts: `docs/RELEASE-REHEARSAL.md`, `docs/ASSURANCE.md`, `release/manifest-template.json`, `tools/package-check/`.

Acceptance criteria:

- Fresh proof/replay and exact native/platform closure evidence accompanies the archive/package.
- Linux x86-64 install smoke path and user-selected pinned oracle are documented; macOS support is not assumed.
- License/secret/artifact inspection and release-blocking finding disposition complete; exact-token-only alpha explicitly disables binary64 claims if that milestone is unready.
- Binary64-enabled alpha additionally requires VJ-034 through VJ-037; unbuilt optional claims cannot appear enabled in the package manifest.
- Every enabled binary64 release claim additionally requires VJ-055 API/codec/artifact binding evidence.

Human review: Release owner plus independent assurance and package review.

Intended capstones: none. Required gates: G00, G02, G05, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-043.json).

### VJ-044 Implement pure approved-result cache model and theorem

Class: `implementation-with-proofs`. Phase: P7. Prerequisites: VJ-006, VJ-031, VJ-032, VJ-053, VJ-054.

Model exact identity, immutable approved outcomes, quotas and safe miss/cancellation behavior.

Allowed files and artifacts: `lean/VerifiedJson/Impl/CheckedCacheModel.lean`, `lean/VerifiedJson/Proofs/CheckedCacheModel.lean`.

Acceptance criteria:

- A hit returns a bound approved result or requires comparison before candidate output release.
- Rebuild/profile/protocol/result identity changes cannot reuse stale approval; exact-key behavior is specified independently of hash indexing.
- Timeout/unsupported/infrastructure/mismatch entries are never promoted into semantic approval.

Human review: Independent maintainer review of contract preservation and submitted evidence.

Intended capstones: J15. Required gates: G00, G01, G02, G03, G04, G05, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-044.json).

### VJ-045 Prepare bounded checked-runtime cache implementation pilot

Class: `maintainer-contract-release-infrastructure`. Phase: P7. Prerequisites: VJ-044, VJ-038, VJ-043.

Implement process-local memory-only cache and explicit checked mode with a tested/native boundary.

Allowed files and artifacts: `crates/json-checked/`, `tests/checked-runtime/`, `docs/CHECKED-RUNTIME.md`.

Acceptance criteria:

- Fault injection covers candidate-changing-output, forged/colliding index, worker failure, single-flight cancellation and full cache.
- No oracle-unavailable fail-open switch or unbounded pending approval exists; no application request waits for patch/network reporting.
- Deep result ownership/destruction, exact build identities and candidate isolation/trust assumptions are reviewed.

Human review: Independent runtime/native boundary audit; pure model proof is not asserted as Rust refinement.

Intended capstones: J15, J16. Required gates: G00, G02, G05, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-045.json).

### VJ-046 Benchmark unique-input checked workloads and limits

Class: `tests-docs`. Phase: P7. Prerequisites: VJ-045.

Measure complete cold/warm, repeated/all-unique and adversarial workload costs.

Allowed files and artifacts: `benchmarks/checked/`, `docs/PILOT-BENCHMARKS.md`.

Acceptance criteria:

- Input/build identities and latency distribution, RSS/allocation, cache quotas, hit rates and timeouts are recorded.
- Candidate-only, oracle-only, checked miss/hit and rerun-plus-comparison modes are separated.
- Thresholds are selected from measured pilot evidence; no production support or shape-certification claim follows from repeats.

Human review: Performance/security owner decides acceptable pilot limits.

Intended capstones: none. Required gates: G00, G02, G05, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-046.json).

### VJ-047 Prepare offline feedback and approved reporter qualification

Class: `maintainer-contract-release-infrastructure`. Phase: P8. Prerequisites: VJ-041, VJ-045, VJ-046.

Prepare separate local queue/export tooling and a qualification plan before any network reporting.

Allowed files and artifacts: `docs/FEEDBACK.md`, `tools/report-drafts/`, `tests/reporting/`.

Acceptance criteria:

- Library has no reporter credentials; raw production data stays local and minimized is not synonymous with anonymous.
- Allowlist, bounded bodies, deduplication, sensitive/security triage and uncertain-post reconciliation are tested using fakes.
- External issues/PRs require explicit operator posting authority and target policy; no code download/automatic production repair occurs.

Human review: Privacy/disclosure and reporter-authority review.

Intended capstones: none. Required gates: G00, G02, G05, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-047.json).

### VJ-048 Qualify one safe-Rust fast path via extraction and refinement

Class: `implementation-with-proofs`. Phase: P9. Prerequisites: VJ-032, VJ-038, VJ-045, VJ-053, VJ-054.

Test extraction feasibility and prove one tiny named domain such as a fixed literal with bounded whitespace.

Allowed files and artifacts: `crates/json-fastpath/`, `lean/VerifiedJson/Proofs/RustFastpath.lean`, `compatibility/rust-extraction.json`.

Acceptance criteria:

- Supported Rust subset/extractor/source/compiler identities are exact and its assumptions recorded.
- An all-input theorem covers the named predicate; unsupported inputs demonstrably fallback.
- Cached observations and seeded-test success cannot replace refinement; broadened domains require new packets.

Human review: Extraction/native trust review and theorem-domain semantic review.

Intended capstones: J16. Required gates: G00, G01, G02, G03, G04, G05, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-048.json).

### VJ-049 Prepare official Lean upgrade and stable qualification candidate

Class: `maintainer-contract-release-infrastructure`. Phase: P10. Prerequisites: VJ-002, VJ-042, VJ-043.

Reuse manual/scheduled GitHub Actions to prepare exact-pin upgrade candidates without deploying them.

Allowed files and artifacts: `docs/TOOLCHAIN-MAINTENANCE.md`, `.github/workflows/lean-upgrade.yml`, `.github/workflows/qualify-stable.yml`.

Acceptance criteria:

- Official RC/stable discovery and best-effort schedule behavior are explicit; no moving selector executes proofs.
- Final stable bytes get new build/replay/semantic and package qualification even if RC source appears unchanged.
- Unavailable checkers/dependency drift become owned blockers; no semantic repair is smuggled through a version bump.

Human review: Workflow/semantic-drift review; hosted enablement remains a separate phase.

Intended capstones: none. Required gates: G00, G02, G05, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-049.json).

### VJ-050 Freeze downstream compatibility and stable release checklist

Class: `maintainer-contract-release-infrastructure`. Phase: P10. Prerequisites: VJ-043, VJ-049.

Prepare independent versioning, first downstream smoke matrix and manual promotion requirements.

Allowed files and artifacts: `docs/STABLE-RELEASE.md`, `docs/COMPATIBILITY.md`, `release/stable-manifest-template.json`.

Acceptance criteria:

- Each claimed API/profile/platform has evidence or an explicit exclusion; binary64 and runtime claims cannot borrow core evidence.
- Packaged source/bytes, dependency/feature closure and release identity are pinned; partial publication reconciliation is planned.
- Only authorized qualified artifacts may promote; optional P7–P9 products are not prerequisites for a correctly scoped core/comparison stable channel.
- If checked-runtime support is claimed, VJ-044 through VJ-046 are additional required evidence; optional runtime does not block the core/comparison stable channel.

Human review: Release owner and independent contract/native/package assurance approval.

Intended capstones: none. Required gates: G00, G02, G05, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-050.json).

### VJ-051 Qualify a minimum current-Lean comparator and replay envelope

Class: `maintainer-contract-release-infrastructure`. Phase: P1. Prerequisites: VJ-004, VJ-054.

Inspect and qualify selected existing comparator/export/replay tools for the initial packet kinds without using an unbuilt project wrapper to certify itself.

Allowed files and artifacts: `docs/VERIFIER-ENVELOPE.md`, `verification/envelopes/**`.

Acceptance criteria:

- Freeze exact comparator/exporter/checker/compiler/dependency identities and minimum module footprint on the chosen Lean lane.
- Valid proofs and actual invalid/axiom/changed-target cases are distinguished by the real tools; unsupported layers remain infrastructure failures.
- Known worker-descendant/export race and primitive/string handling limits are either repaired and tested or block qualification.
- Manual independent review records scope; compatibility of each later new declaration/runtime domain is requalified.

Human review: Independent bootstrap/boundary review and applicable empirical checks; mathematical claims need qualified packet gates.

Intended capstones: none. Required gates: G00, G01, G02, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-051.json).

### VJ-052 Implement the bounded submission supervisor adapter

Class: `maintainer-contract-release-infrastructure`. Phase: P1. Prerequisites: VJ-051, VJ-008.

Adapt qualified existing comparator interfaces under a small trusted supervisor; no new theorem-comparison engine or claim service.

Allowed files and artifacts: `tools/verify-ticket`, `tools/verification/**`, `tests/verification/**`.

Acceptance criteria:

- Frozen source and policy are reconstructed independently; candidate PR paths map to a separate generated submission workspace.
- Untrusted elaboration has no credentials/network/shared writable cache; all descendants terminate before outputs are sealed.
- A separate verifier inspects bounded sealed artifacts and emits source-bound stage evidence with PASS/REJECT/INFRA.
- Local positive/negative/fault tests and independent code review establish the supervisor boundary; no formal self-certification is asserted.

Human review: Independent bootstrap/boundary review and applicable empirical checks; mathematical claims need qualified packet gates.

Intended capstones: none. Required gates: G00, G01, G02, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-052.json).

### VJ-053 Qualify the operational mathematical submission gate

Class: `maintainer-contract-release-infrastructure`. Phase: P1. Prerequisites: VJ-052, VJ-051.

Run the real end-to-end gate on positive/negative submissions before opening the first mathematical tickets.

Allowed files and artifacts: `tests/verification/canaries/**`, `verification/envelopes/**`, `docs/VERIFIER-QUALIFICATION.md`.

Acceptance criteria:

- Actual valid proof/implementation examples pass and direct/hidden placeholders, extra axioms, target drift and disabled kernel checks cannot pass.
- Race/sealing, forged/stale artifacts, missing checker, malformed protocol, unsupported exports and failed writes produce the declared safe verdicts.
- Publish an exact qualified validator.argv and envelope identity only for supported packet kinds and pins; no production theorem exists by inference.
- Bootstrap uses manual review plus real empirical checks; it does not depend on its own mathematical PASS.

Human review: Independent bootstrap/boundary review and applicable empirical checks; mathematical claims need qualified packet gates.

Intended capstones: none. Required gates: G00, G01, G02, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-053.json).

### VJ-054 Prepare the Lean and Rust workspace skeleton

Class: `maintainer-contract-release-infrastructure`. Phase: P0. Prerequisites: VJ-001, VJ-002.

Prepare a source-only buildable package skeleton with exact current toolchain identities and no parser/proof claims.

Allowed files and artifacts: `lean/lakefile.toml`, `lean/lean-toolchain`, `lean/lake-manifest.json`, `lean/VerifiedJson.lean`, `Cargo.toml`, `crates/json-contract/Cargo.toml`, `crates/json-contract/src/lib.rs`, `docs/BUILD.md`.

Acceptance criteria:

- Lean package/root targets and Rust workspace members/build boundaries are declared explicitly.
- A minimal fresh source-only build smoke test runs under the selected stable/RC pins without placeholder or parser correctness claims.
- No hidden build download, reporter, publication action or private path is introduced; setup ownership and dependencies are explicit.

Human review: Independent bootstrap/boundary review and applicable empirical checks; mathematical claims need qualified packet gates.

Intended capstones: none. Required gates: G00, G01, G02, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-054.json).

### VJ-055 Bind binary64 operations into the public oracle and transport

Class: `implementation-with-proofs`. Phase: P4. Prerequisites: VJ-036, VJ-037, VJ-032, VJ-031, VJ-053, VJ-054.

Connect admitted numerical operations to the exact exported oracle API and codec, preserving the separately reviewed numeric profile contract.

Allowed files and artifacts: `lean/VerifiedJson/Impl/OracleApi.lean`, `lean/VerifiedJson/Proofs/OracleApi.lean`, `lean/VerifiedJson/Proofs/NumericTransport.lean`, `tests/numbers/oracle/**`, `compatibility/numeric-api.json`.

Acceptance criteria:

- Freeze the approved numeric API/profile revision and explicit dispatcher implementation holes before mathematical work.
- Recompose J16 and the numeric J17 branch to the actual J12/J13 operations; compiled closure contains the qualified provider and no unchecked substitute.
- Signed-zero, ties, range/underflow and disabled-profile cases survive the exported operation and neutral codec on the built oracle.
- Numeric cells and release claims stay disabled until this API/artifact binding evidence is accepted.

Human review: Independent bootstrap/boundary review and applicable empirical checks; mathematical claims need qualified packet gates.

Intended capstones: J12, J13, J16, J17. Required gates: G00, G01, G02, G03, G04, G05, G06, G07, G08, G09.

Status: candidate template; no live claim or qualified target. [Individual packet](../work-packets/VJ-055.json).
