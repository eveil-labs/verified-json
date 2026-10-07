# Verified JSON

Verified JSON is a candidate Lean implementation of JSON with explicit parsing, serialization and numerical contracts, plus tools for comparing existing implementations against that reference. The first comparison target is Rust's serde_json. Community contributions can use any LLM, provided the resulting work satisfies a frozen packet and independently checked proof obligations.

The local bootstrap now includes a complete-document byte parser, serializer,
lossless wire AST, bounded oracle prototype, Rust codec/comparison tools and a
fail-closed packet preflight. The first narrow source proofs cover cursor and
accepted number-token properties. Complete parser correctness, the independent
full-document relation, transport correctness and release qualification remain
open. There is no qualified untrusted submission gate or release;
all 55 community packet templates remain NOT_READY. Native GitHub tracking is live in the
[Draft board](https://github.com/orgs/eveil-labs/projects/1/views/2) and
[issues](https://github.com/eveil-labs/verified-json/issues).

Start with [build instructions](docs/BUILD.md), the compact [draft contract](docs/SPEC.md)
and [current implementation/coverage status](docs/STATUS.md). The independent
[full document contract draft](docs/CONTRACT-REVIEW.md) is awaiting human semantic
review; its 24 witnesses are separate from the 17 implementation-helper roots. Build/tests create
artifacts only in an explicitly selected scratch directory, never under this
source project.

## Development and contribution documents

- [Development plan](docs/DEVELOPMENT.md): phases, architecture and acceptance gates.
- [Individual tickets](docs/TICKETS.md): bounded tasks and prerequisites.
- [Machine readable ticket index](work-packets/TICKETS.json): ticket templates; each ready ticket will also have its own frozen packet.
- [Contribution guide](CONTRIBUTING.md): the human workflow and submission evidence.
- [Instructions for coding agents](AGENTS.md): read this before asking an LLM to contribute.
- [Six hour claims](docs/CLAIMS.md): native GitHub coordination and deadline convention.
- [Submission verification](docs/VERIFICATION.md): checker reuse, proof scope and qualification requirements.
- [GitHub feature reuse](docs/GITHUB-REUSE.md): existing features used now and automation deferred until later.
- [Verifier assessment](docs/TOOL-ASSESSMENT.md): existing tool capabilities and remaining qualification work.

## What contributors can take on

Maintainers first approve the independent wire specification, result categories and profiles. They then publish small packets with stable identifiers, exact target statements, allowed implementation holes, allowed files and an executable validator configuration. A Ready issue points to one immutable packet revision. The issue and Project board track coordination; the committed packet defines the task.

Proof-only contributions fill proof bodies without changing the theorem, its hypotheses, or the definitions that give it meaning. Implementation-with-proofs contributions may change explicitly designated implementation bodies and must prove the supplied total correctness obligations. Specifications, verification infrastructure, numeric contracts and releases receive separate maintainer review.

## Initial scope

The wire representation preserves object member sequences, duplicate names, number tokens and UTF-16 code units. A planned strict application profile will check scalar strings and duplicate-key policy. The planned binary64 bridge has explicit rounding, signed-zero and range outcomes. The complete-document parser consumes all bytes apart from permitted surrounding whitespace.

Development follows the current official Lean release candidate, with the latest stable compiler tested for compatibility in a separate lane. FloatLib is planned through the minimum qualified import and runtime closure; the current exact-token byte core imports none. Exact toolchain and dependency identities come from the current trusted packet; a contributor never substitutes a moving latest selector into a submitted result.

The parser, oracle transport, Rust projection and cache carry separate assurance claims. Comparing one Rust run with Lean does not prove all Rust executions. Runtime feedback and repair workers remain optional later products; the library has no reporter credentials and never installs its own generated patch.

## Coordination now

Use native GitHub Issues, sub-issues, blocked-by relationships, assignees, milestones and a Project board. A contributor asks for a six-hour reservation in a comment and waits for maintainer assignment and acknowledgment. Deadline expiry is handled manually at first. There is no live `/claim` command or claim bot in this scaffold.

Six hours limits how long a courtesy reservation blocks others; it is not an estimate that every task can be finished in six hours. Preserve partial work and request a smaller task or a renewal when appropriate. A claim never grants merge authority or changes proof acceptance rules.

## Release claims

Publish source properties only after frozen statements, fresh builds, transitive axiom checks and required kernel replay pass. State compiler, runtime, native helper, adapter and operating-system assumptions separately. A green GitHub check means exactly the published gate it ran; it is not a substitute for a correct specification or broader runtime guarantee.
