# Native GitHub tracking

[Repository](https://github.com/eveil-labs/verified-json) ·
[Work packets board](https://github.com/orgs/eveil-labs/projects/1/views/2) ·
[Issues](https://github.com/eveil-labs/verified-json/issues)

The operator authorized public setup. The initial native backlog contains 55
Draft ticket issues, 11 phase parents/milestones, 55 sub-issue links and 200 blocked-by
relationships from the source DAG. Each ticket links to its immutable initial
template at the bootstrap source commit. Later Ready packets need a separate
reviewed revision and qualified gate. No issue is claimable merely because it
appears on the board.

The Project is public, linked to this repository, and has a native board view.
Its Status options are Draft, Blocked, Ready, Claimed, In Progress, In Review and
Done. All initial items are Draft. Native labels identify task class, milestones
identify phases, and text fields record Packet, Claim Expires UTC and Claim
Record. No claimant or expiry is recorded initially.

Claims are manual six-hour courtesy reservations under docs/CLAIMS.md, using
issue comments and assignees. No bot or separate tracking service is enabled.
Readiness, proof acceptance and merge/release decisions remain distinct.

The hosted Linux bootstrap workflow passed after the initial source push. Its
name and result explicitly describe candidate build/tests rather than proof
admission. Darwin independent-replay manifests do not qualify Linux kernels or
the untrusted contribution envelope.
