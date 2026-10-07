# Draft VJ1 neutral protocol

This transport is independent of the JSON parser being compared. Its current
implementation is a prototype; J17 lossless-codec proof remains open.

One request process receives one ASCII hex line encoding JSON input bytes, then
EOF. Hex may use either case; spaces inside the line are invalid. The request
length is bounded by twice the JSON input-byte budget plus a newline. Empty hex
is an empty JSON document.

Exactly one response line is written:

```text
VJ1\tok\t<hex encoded AST>
VJ1\terr\t<syntax|utf8|limit|unsupported>\t<decimal byte offset>
```

The Lean CLI may return transport for malformed request framing; callers classify
that as infrastructure rather than JSON syntax. Diagnostics belong on stderr.
There is no JSON parsing involved in this envelope.

## Binary AST

Every length is a four-byte unsigned little-endian integer. Strings contain raw
16-bit units, also little-endian. Decode must consume the entire buffer.

| Tag | Payload |
| --- | --- |
| 0 | null, no payload |
| 1 | false, no payload |
| 2 | true, no payload |
| 3 | number ASCII byte count, followed by token bytes |
| 4 | UTF-16 unit count, followed by units |
| 5 | array element count, followed by AST elements |
| 6 | object member count, followed by members in order |

Each object member is an untagged UTF-16 key (unit count then units), followed by
one AST value. Repeated keys remain repeated. Byte lengths, declared lengths,
depth, total nodes, units and number bytes are checked before allocation in the
Rust decoder. A host integer conversion or u32 length overflow must be rejected.
No Rust adapter may reinterpret a transport error as an input syntax error.
