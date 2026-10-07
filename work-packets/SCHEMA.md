# Work packet template and activation rules

The current JSON files are individual planning templates, not executable tickets. Every `claim_ready` is false and actual revision, declaration, dependency and validator identities are unset. The index is a static machine-readable view of these templates. Live coordination belongs to native GitHub issues and Projects, not to editable reservation fields in packet files.

## Template fields

- `id`, `title`, `phase`, `ticket_class` and `prerequisites` define the bounded planned task.
- `goal`, `acceptance_criteria`, `capstones`, `required_gates` and `human_review` define intended acceptance.
- `allowed_files`, `read_only_contract_paths`, `scope_rule`, selectors and bindings constrain changes.
- Source, contract, toolchain and validator fields identify actual trusted inputs after activation.
- `claim_hours` is six; `implementation_estimate_hours` is null because a reservation is not a measured completion estimate.
- `validator.kind`, `validator.status`, `validator.argv` and `validator.identity` separate an unqualified template, a frozen manual review policy and a qualified executable Lean gate.

## Activation by maintainers

First inspect prior work and satisfy the actual accepted dependency outputs, rather than treating an issue's closure as proof. Split broad packets before opening reservations. Freeze source, scope, target meaning, profiles, examples and acceptance policy at a reviewed source revision; record the content identity using the project's published canonicalization recipe. A contributor cannot activate a packet by editing it in their own PR.

For proof-only or implementation-with-proofs work, activation requires actual target names and elaborated type/definition bindings, exact dependency/compiler/checker identities, the applicable gate qualification evidence, and a non-null exact `validator.argv`. `validator.status` becomes READY only after that envelope is qualified. Definition-hole lists are empty for proof-only work and explicit for implementation work.

For maintainer-contract-release-infrastructure and tests-docs tasks, activate a frozen review checklist and relevant empirical checks. Use a manual-review validator kind where appropriate; mathematical targets that do not apply have explicit reasons rather than fabricated declarations. A bootstrap checker ticket cannot validate itself as a mathematical proof of its own correctness. Ready status for these classes authorizes a scoped proposal, not automatic proof or release acceptance.

All required applicable gates must actually run or be reviewed as specified. A stage may be declared not applicable only in the frozen class-specific policy with a reason; a contributor cannot retrospectively skip a failed or unavailable required stage. Unsupported or missing checks remain infrastructure failures.

Create the native issue/sub-issue and blocked-by relationships during the authorized repository setup phase. Link to the exact packet file revision and identity. A maintainer may then mark the coordination issue Ready and acknowledge a reservation. The acknowledgment does not change the immutable packet contract or grant merge authority.

## Packet changes and index consistency

The per-ticket file becomes the authoritative committed contract at activation. Regenerate the static index and human backlog from those committed packets; do not maintain a separate dynamic tracker. Any revision to frozen meaning, allowed paths, dependency identities or acceptance policy creates a new packet revision and invalidates stale submission evidence. Existing drafts remain preserved and may be revalidated against the new contract.

GitHub issue URLs and Project fields are coordination references. They cannot redefine target types, alter proof policy or substitute a moving branch for a frozen source identity. Active lease state remains in native assignment/comment history, with manual deadline management initially.
