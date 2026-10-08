# Draft Rust wire codec and comparison CLI

This bootstrap contains a dependency-free `json-wire` codec and a separate
`verified-json-diff` CLI. Both are candidate native implementations with tests. No J14,
J17, machine-code, sandbox, binary64, or runtime-cache proof is claimed.
Version `0.1.0-rc.1` identifies local candidate source; it is not a published release.
The bootstrap Rust requirement is 1.96, the tested toolchain, rather than an
untested minimum-version promise.

## Neutral representation

`WireValue` preserves object member order and duplicates, exact ASCII number
tokens and UTF-16 string/key units, including unpaired surrogates. It discards
source whitespace and escape spelling. Its binary codec uses:

| Tag | Payload |
| --- | --- |
| 0 | null |
| 1 | false |
| 2 | true |
| 3 | u32 little-endian byte count, then ASCII JSON number token |
| 4 | u32 little-endian unit count, then u16 little-endian string units |
| 5 | u32 little-endian child count, then child nodes |
| 6 | u32 little-endian member count, then untagged key-unit count/units and value for each member |

Decoder success requires full consumption. Invalid tags, truncated fields,
invalid number tokens and trailing bytes are codec errors. Resource refusals
have distinct limit categories. The implementation charges values plus one
additional node unit per object member. String/key units share one total budget.

Default wire budgets are 8 MiB encoded bytes, root-depth zero with maximum depth
128, 100,000 value/member units, 2,097,152 total string/key units, and 4,096 bytes
per number. Configured recursive depth over the native ceiling 256 is refused.
These are draft operational limits, not formal resource guarantees. A caller
constructing an arbitrary deep AST outside decoder-controlled APIs remains
responsible for its ownership/destruction behavior.

## Candidate comparison profile

The manifest pins `serde_json = 1.0.151`, inspected from its official source and
resolved from crates.io, plus `serde = 1.0.229`; Cargo.lock records registry
checksums and complete resolution. Unix subprocess I/O uses exact `rustix = 1.1.5`
with only `std`, `fs` and `process` features. Requested serde_json features are `std` and
`raw_value`. Record the effective feature tree when checking a build, since
Cargo feature unification can change it. [Official serde_json manifest](https://github.com/serde-rs/json/blob/master/Cargo.toml)

The adapter deserializes each value through `RawValue` before conversion, uses
sequence/map visitors rather than `serde_json::Value`, and copies numeric token
bytes without conversion. This retains member order and duplicates and avoids
the default float parser's accuracy/range contract. It makes no binary64 or
correct-rounding claim. Native strings/keys are decoded by serde into scalar
strings and re-encoded as UTF-16. Lone escaped surrogates are consequently a
known application-profile difference from the wire oracle. [RawValue API](https://docs.rs/serde_json/1.0.151/serde_json/value/struct.RawValue.html)

Input is capped at 1 MiB. Candidate AST construction uses the codec's value,
unit and token budgets, but caps recursive depth at 64. A lexical nesting
preflight prevents deeply nested input from reaching the candidate's RawValue
scanner. This refusal is a limit outcome, even when the same input is also
syntactically malformed. The serde reader's own rejection remains candidate
diagnostic evidence; rejection coordinates from nested raw subvalues need not
be absolute coordinates in the original document. The draft adapter may parse
the same subtree more than once; its performance is not qualified.

## Oracle subprocess protocol

The CLI invokes only the explicitly supplied oracle path, resolved to a regular
file. It writes one ASCII input-hex line containing immutable original JSON
bytes, closes stdin, and expects exactly one response line:

```text
VJ1<TAB>ok<TAB>NEUTRAL_AST_HEX
VJ1<TAB>err<TAB>CODE<TAB>ABSOLUTE_INPUT_BYTE_OFFSET
```

Codes are exactly `syntax`, `utf8`, `limit`, `unsupported`, and `transport`.
Unknown codes, malformed fields,
offsets beyond the input, mixed diagnostics on stdout and malformed AST frames
are protocol failures. `utf8` is a syntax rejection; `transport` is infrastructure.

Default deadline is 2 seconds, selectable up to 60 seconds. Stdout is capped at
twice the wire-byte budget plus 96 framing bytes; stderr is capped at 64 KiB.
Writing stdin, reading both output streams and process completion share the
deadline through a thread-free nonblocking loop. Caller-owned pipes close before
cleanup, even if an escaped descendant retains its ends. Child environment is
cleared except a fixed system PATH and LANG. On Unix the child starts in its own
process group. Completion is observed with `waitid(WEXITED | WNOHANG | WNOWAIT)`,
which keeps the leader waitable and reserves its process ID even after exit.
After a successful response with exit zero and EOF on both output streams,
cleanup only reaps the direct child; it sends no signal. This does not establish
that silent descendants are absent. On failure, timeout or an output cap,
cleanup checks waitable ownership, signals the group and direct child **before**
the first reap, then observes direct-child reaping. Cleanup has a separate 250 ms
budget. No later signal is sent after reaping releases the ID. A missing
waitable identity (`ECHILD`) refuses signaling and is infrastructure failure;
missing cleanup evidence is likewise infrastructure failure.
Group-signal errors retain their native error code and still trigger bounded
direct-child fallback. When a request already has a limit/protocol failure and
cleanup also fails, both observations are retained; the limit is not relabeled
as syntax. Successful response bytes require observed direct-child reaping before
the call returns success. Negative lifecycle fixtures separately check the primary
failure and require observed direct-child reaping; they do not establish that
every descendant was contained or killed.
The embedding application must give this call exclusive reaping ownership of
its child and must not ignore `SIGCHLD` or enable automatic child reaping
(`SA_NOCLDWAIT`). An unrelated thread/signal handler consuming the child's status
breaks that precondition; this API cannot prevent another reaper's actions. The
standalone CLI does not install such a handler. The pinned safe rustix process
surface does not inspect process-wide signal dispositions; observed loss of
waitable ownership is refused rather than treated as successful cleanup.
On macOS, group signaling can return `EPERM` for a group containing only zombies;
the failure path retains that uncertainty instead of treating every `EPERM` as
proof that no live descendants remain. The completed-exchange path needs no group
signal and makes no such descendant claim.
[Darwin group-signaling implementation](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/kern/kern_sig.c).
The API does not spawn detached I/O workers. This is native lifecycle management, not an
adversarial sandbox: an executable can deliberately escape its group. There is
no OS memory cap or guarantee against side effects of the chosen executable.
The parent validation/release envelope must bind the oracle executable digest,
compiler/runtime/target and protocol identity; this draft CLI does not enforce
a cryptographic artifact pin or prevent path replacement races. The nonblocking
transport requires Unix and the pinned rustix non-reaping wait/status APIs;
platforms lacking them refuse before spawning. Linux and macOS expose the required
APIs. Current execution evidence is for the local test
platform, with other supported-platform qualification still required. The safe
native syscall boundary is rustix and the operating system.
[Nonblocking I/O](https://docs.rs/rustix/1.1.5/rustix/fs/fn.fcntl_setfl.html),
[non-reaping process observation](https://docs.rs/rustix/1.1.5/rustix/process/fn.waitid.html).

## Invocation and observations

Allocate Cargo home, target and test scratch outside the source checkout before
building. For example, use caller-selected central WORK directories:

```sh
CARGO_HOME="$VJ_CARGO_HOME" CARGO_TARGET_DIR="$VJ_CARGO_TARGET" \
  VERIFIED_JSON_TEST_WORK="$VJ_TEST_WORK" cargo test --workspace --locked --offline
"$VJ_CARGO_TARGET/debug/verified-json-diff" --oracle "$VJ_ORACLE" --input sample.json
"$VJ_CARGO_TARGET/debug/verified-json-diff" --oracle "$VJ_ORACLE" --hex 6e756c6c
```

Without `--input`/`--hex`, stdin is the bounded JSON-byte input. Output is a
metadata-only JSON observation; it does not echo application data. The tool has
no reporter or automatic repair behavior.

Exit 0 means observed exact wire agreement or that both implementations rejected;
`both_rejected` does not assert identical reasons. Exit 2 is an observed
discrepancy, 3 infrastructure/protocol failure, 4 an operational input/output or
candidate/oracle limit, 5 a known scalar-profile difference or oracle unsupported
case, and 64 invalid invocation or invalid input-hex encoding. Input file I/O
failure is infrastructure, not a JSON rejection. A discrepancy is not automatically an upstream
bug. No observed agreement establishes an all-input theorem or authorizes an
unchecked future candidate execution.

Tests cover exact codec round trips, every truncated prefix of a compound frame,
invalid tags/numbers/counts, resource boundaries, request/response framing,
duplicate order, exact exponent spelling, huge-but-short exponent tokens, lone
surrogate profiles, missing/blocked workers, bounded output and seeded CLI
discrepancies. Shell oracle fixtures are explicitly fake protocol peers; actual
Lean-oracle integration is separately recorded by the parent.
Lifecycle regressions check signal-before-reap ordering through an operation
seam, loss-of-identity refusal, combined failures, repeated observation of a real
waitable child, and pipe-holders after leader exit. Detached fixtures terminate
through their own bounded release protocol; tests do not force PID reuse or
signal unrelated processes.
