# Local implementation status

Candidate source, not a release. Community tickets remain NOT_READY; the compact
wire contract is a review draft. The public repository and native Draft issues/Project are configured. No automatic
merge/reporting authority is enabled.

## Implemented candidate behavior

- Dependency-free Lean wire AST with exact numeric tokens, ordered duplicate
  object members and UTF-16 code-unit strings.
- Safe cursor and independent decimal-token grammar/recognizer.
- Total fuel-bounded complete-document parser with strict raw UTF-8, escapes,
  arrays, objects, trailing-input rejection and configurable structural limits.
- ASCII serializer rejecting invalid handcrafted number tokens.
- One-request bounded oracle prototype and lossless neutral AST representation.
- Rust wire codec and an offline serde_json comparison CLI retaining sequence
  observations and exact tokens, with scalar-string profile distinctions.
- Nonexecuting fail-closed work-packet/source metadata preflight.
- Native GitHub bootstrap CI source, 55 work-packet templates and agent guidance.

## Source proofs

proofs/roots.json names 17 candidate roots. They establish cursor EOF/progress,
accepted-token grammar, exact input-span preservation, token-budget/end bounds,
concrete lexical witnesses, BMP scalar-unit encoding and the fixed width of
a serialized UTF-16 escape. These are useful bounded steps, not complete JSON
correctness. Axioms are restricted to propext, Quot.sound and Classical.choice.

## Observed bootstrap results

A fresh RC build, all 17 transitive-axiom root audits and whole-import-closure
same-kernel replay passed. The parent suite passed 22 Python cases (9 native
oracle test methods and 13 packet-preflight cases) and 22 Rust cases. Four additional trusted-replay boundary tests passed after
the adapter was added. Seven
synthetic cross-language comparisons produced the expected agreement, shared
rejection, scalar-profile difference and candidate-limit observations. Latest
stable 4.34.1 built the same source and passed the 22 Python cases.

Independent replay is scoped to the exact 17 exported proof roots and primitive
basis; it does not establish full parser or native correctness. The known
unchecked-False canary was rejected. Broader primitive-footprint and adversarial
supervisor qualification remain open. The hosted Linux bootstrap workflow passed; this does not qualify proof admission.

## Still open

The independent full-document byte/AST relation and human review; complete
UTF-8/escape proofs; number grammar completeness/progress; whole-parser
soundness/completeness; fuel adequacy and resource model; serializer and neutral
codec round trips; native API/refinement binding; qualified adversarial
submission supervisor; and minimal FloatLib/binary64 admission. Runtime cache,
feedback/reporting and automatically repaired Rust are later phases.

## Checks and assumptions

Lean development pin is 4.35.0-rc4, with 4.34.1 separately tested for source/native
compatibility. Rust bootstrap compiler is 1.96.0. All generated artifacts are
kept in caller-selected central work directories. Complete identities/logs are
retained by the local parent workcell, rather than embedded as machine-private
paths in this public project.

Axiom audits, same-kernel replay, independent replay, behavior tests and release
acceptance have different scopes. Native execution assumes compiler/runtime/OS
correctness. Current subprocess bounds do not constitute an adversarial sandbox.
The preflight deliberately has no mathematical PASS path. Stable promotion,
public invitation and publication require the remaining qualification/review.
