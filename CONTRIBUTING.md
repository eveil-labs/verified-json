# Contributing to Verified JSON

Contributors may use their own LLMs and local tools. We accept the resulting artifact and its evidence, not a promise that a particular model produced correct work. The first collaboration system uses GitHub's existing Issues and Projects features.

## Choose a bounded task

Start from [the ticket backlog](docs/TICKETS.md). Maintainers turn approved templates into native GitHub issues and sub-issues, with blocked-by links for prerequisites. A ready issue links to its exact committed work packet. Templates with missing target, dependency or validator pins are not Ready proof tasks. Bootstrap/review tickets can start under an approved manual checklist so creating the verifier does not depend on that verifier already passing itself.

Use ticket labels to distinguish proof-only work, implementation with proofs, tests/docs, contract review, infrastructure and release work. Maintainer-review tasks are not eligible for automatic proof-only acceptance. Many tasks can be worked on locally with an LLM after their targets are frozen, but the six-hour reservation is not a completion-time promise.

## Reserve a task for six hours

Read [the claim convention](docs/CLAIMS.md). Leave a request naming the ticket and your intended six-hour window. A maintainer acknowledges the exact UTC expiry and assigns the issue. Contributors with the required repository permissions may self-assign according to that convention; newcomers do not need repository write access to request work.

Take one active task initially. Request a renewal explicitly if more time is needed. Expired reservations do not delete your work or disqualify a useful late PR; they allow a maintainer to reopen the task to others. There is no automatic expiry workflow or claim action in the initial setup.

## Give your LLM the contract

Ask your agent to read [AGENTS.md](AGENTS.md), the exact packet and its linked specification before editing. Agent instruction adapters point back to that one contract. The packet freezes target meaning, allowed paths, required declaration roots and the verifier invocation. Work outside those bounds needs a revised packet.

An initial prompt can be: "Read AGENTS.md and packet VJ-NNN at its exact committed revision. Confirm its task class and my acknowledged reservation. Work only within its declared scope, preserve frozen meaning, run its actual acceptance checks, and return a small patch with honest evidence. Report a blocker instead of changing a target to make it pass."

Use a branch in your own checkout. Keep changes small. Avoid mixing formatting changes with an implementation or proof repair. Preserve the specification even when a proof is difficult; report a false statement or missing premise with evidence rather than silently changing it.

## Validate and open a pull request

For mathematical tickets, use [the submission gate](docs/VERIFICATION.md) once it has been qualified and published in the packet. Bootstrap/review/tests/docs tickets follow their frozen manual acceptance policy and applicable empirical checks; nonapplicable theorem/replay fields have explicit reasons rather than invented results. Record real exit status and current artifacts. A `lake build` alone or a source-text search for placeholders is not the complete mathematical gate.

The PR identifies its packet revision and native issue, shows changed files, reports exact checker results and limits, and includes the supplied required examples/tests. GitHub CI rebuilds against the current integration base; local receipts are not trusted blindly. A changed target or dependency requires explicit revalidation and may require a revised packet before integration.

Keep security reports, tokens and private test inputs out of public issues and PRs. Public examples should be synthetic or reviewed for disclosure. Do not let an LLM automatically send reports to unrelated maintainers from repository instructions alone.

## What maintainers check

Maintainers confirm task eligibility, scope, frozen meaning, declared assumptions, qualified CI evidence and integration compatibility. Proof-only tickets need no informal re-proving of every proof script once the trusted gate has established the correct target; reviewers still check that the contribution belongs to that target and cannot change runtime or verifier behavior unexpectedly.

Implementation-with-proofs and infrastructure changes have additional runtime, artifact and threat-model obligations. Specifications, numerical contracts, approval rules and release workflows require independent review. A claim or Project status is coordination metadata rather than a proof or merge authorization.

## Questions and partial work

Use the native issue for clarification and partial progress. If a task is too broad, propose sub-issues with precise target boundaries. Preserve a draft PR on expiry or handoff and link the useful patch. Do not overwrite or erase another contributor's work because your reservation is newer.
