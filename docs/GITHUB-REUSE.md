# GitHub feature reuse

Use native GitHub features for the initial contributor workflow. No claim bot, custom tracker, database, hosting service or automatic expiry action is introduced. The repository scaffold is prepared documentation; hosted configuration happens during the separate repository setup phase.

## Features used now

| Need | Existing GitHub feature | Project convention |
| --- | --- | --- |
| Development plan and ticket hierarchy | Issues, milestones and sub-issues | One phase parent and one bounded issue per packet |
| Prerequisites | Native blocked-by relationships | Accepted artifact evidence remains required; closing an issue alone is insufficient |
| Coordination board | Projects and built-in status/add workflows | Draft, Blocked, Ready, Claimed, In Progress, In Review and Done |
| Current contributor | Issue assignee and comments | Maintainer acknowledges a six-hour reservation before work is exclusive by courtesy |
| Precise expiry | Comment and optional Project text field | Record whole-second UTC start and expiry; manage expiration manually |
| Task proposals | Native issue forms | Forms do not activate a proof packet or grant a reservation |
| Submission and review | Fork/branch PRs, linked issues, reviewers and required checks | Trusted packet and actual CI evidence govern acceptance |
| LLM context | Root AGENTS.md and small instruction entry points | Keep one source of rules; contributors can use any LLM |
| RC and stable qualification | GitHub Actions and manual workflow dispatch | Planned release workflow, not a new service; final-pin checks precede publication |

Native issue dependencies are distinct from sub-issue hierarchy. Project fields provide views over the same issues rather than a second canonical task database. [Sub-issues](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/adding-sub-issues), [dependencies](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/creating-issue-dependencies), [Project automations](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-built-in-automations)

External contributors can comment to request work; a maintainer with the required repository access assigns them. GitHub permits assignment of prior commenters, among other eligible accounts. A six-hour timestamp goes in a comment/text field because the Date field is a calendar-date facility. [Assignment](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/assigning-issues-and-pull-requests-to-other-github-users), [Date fields](https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields/about-date-fields)

Built-in Project workflows can reflect closed issues or merged PRs as Done. That is coordination metadata; the verified claim manifest establishes accepted proofs. Configure no workflow that turns an unreviewed or blocked packet into Ready. Root AGENTS.md contains the contributor rules; instruction adapters point back to it. GitHub documents repository instruction files and custom agents, but a project does not require contributors to use Copilot. [Agent instructions](https://docs.github.com/en/enterprise-cloud%40latest/copilot/how-tos/copilot-cli/customize-copilot/create-custom-agents-for-cli)

## Six-hour reservations now

[CLAIMS.md](CLAIMS.md) gives the native manual procedure. One active task and one normal renewal are human-managed guidelines. There is no exact deadline scheduler, global quota or automatic claim acknowledgment. Preserve late PRs and partial work. A maintainer resolves simultaneous requests and records handoffs. Claims do not grant merge or proof authority.

## Deferred optional action

The Lean community's [intentions action](https://github.com/leanprover-community/intentions) documents hour-based claim durations, renewal and expiry sweeps. It is a possible later replacement for manual coordination, not an initial dependency. Its schedules are best effort; readiness, prerequisites, cumulative renewal and race behavior need separate qualification. If reconsidered, inspect the exact workflow/action revisions and permissions, and rehearse blocked tasks, expiry, PR transitions and concurrent operations before enabling it. No workflow, token or bot command for it is prepared in this scaffold.

## Proof verification remains a separate concern

GitHub required checks orchestrate validation; they do not themselves check Lean proof meaning. [VERIFICATION.md](VERIFICATION.md) and [TOOL-ASSESSMENT.md](TOOL-ASSESSMENT.md) describe reusing an existing comparator/replay architecture with a small qualified adapter. The initial backlog assigns actual gate implementation and qualification before public mathematical tickets can become Ready.
