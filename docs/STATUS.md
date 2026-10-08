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

proofs/roots.json names 18 candidate roots (the original 17 plus the string start clamp). They establish cursor EOF/progress,
accepted-token grammar, exact input-span preservation, token-budget/end bounds,
concrete lexical witnesses, BMP scalar-unit encoding and the fixed width of
a serialized UTF-16 escape. These are useful bounded steps, not complete JSON
correctness. Axioms are restricted to propext, Quot.sound and Classical.choice.

## Observed bootstrap results

The audit-repair RC build checks 18 implementation helpers, 24 draft contract
witnesses and 32 explicit meaning definitions. Transitive axiom audits and
whole-import-closure same-kernel replay passed. The expanded suite comprises 63
Python cases, 33 Rust cases and 100 native Lean API regression assertions.
The earlier bootstrap also observed cross-language agreement, shared rejection,
scalar-profile differences and candidate-limit behavior. Stable 4.34.1 is checked
separately for compatibility; the development pin remains the RC.

Independent replay now covers both bound root manifests: 18 helpers plus six
implementation meanings, and 24 witnesses plus 26 contract meanings. Each export
passes the official paranoid checker and the independent kernel. This establishes
only the selected declaration closures under the recorded primitive basis, not
full parser or native correctness. The earlier unchecked-False canary was rejected.
Broader primitive-footprint and adversarial supervisor qualification remain open.
The hosted Linux workflow checks the candidate build and tests; it does not qualify
proof admission.

## Still open

The independent full-document byte/AST relation is drafted in DocumentSpec.lean
with 24 witnesses. Human semantic review remains pending; complete
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

The audit repairs add one narrow out-of-bounds helper theorem, numeric validation
at the public transport boundary, bounded identity-safe process lifecycle,
structured large-integer metadata refusal and source-bound bootstrap receipts.
They do not alter the document grammar, approve the spec, or open proof claims.
Diagnostic offsets in the draft are explicitly bounded positions; exact/earliest
ErrorAt semantics are not claimed.
