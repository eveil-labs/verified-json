# Draft wire-v1 contract

Status: local implementation draft awaiting human semantic review. The Lean types
and independent number relation are review targets. Source proofs are candidate
evidence, not admission of this draft or approval of an untrusted submission gate.

## Bytes and values

The input is an immutable finite byte sequence. A document contains one value
with optional JSON whitespace (20, 09, 0A, 0D hex) at either end. Comments, a BOM,
trailing values and trailing commas are rejected by this profile. The grammar
follows [RFC 8259](https://www.rfc-editor.org/rfc/rfc8259), with explicit wire
observations where applications often choose different representations.

The AST has null, booleans, exact number tokens, decoded UTF-16 unit sequences,
arrays and ordered object member sequences. Object entries retain duplicate keys.
These observations preserve distinctions needed for comparison; application
object equality may deliberately ignore order under a separate projection.

Raw string bytes must encode Unicode scalar values in well-formed shortest UTF-8;
raw control characters, surrogates, overlong encodings and values above 10FFFF hex
are invalid. Escaped four-hex-digit units are retained, including unpaired
surrogates. Paired escapes and raw supplementary scalar characters produce the
same two UTF-16 units. No normalization, case folding or key deduplication occurs.

Numbers keep their ASCII spelling: optional minus, zero or a nonzero digit followed
by digits, optional fraction with at least one digit, optional exponent with
optional sign and at least one digit. Leading plus/zeros, NaN, infinity and an
incomplete fraction/exponent are invalid. No conversion to machine floats occurs.

## Limits and outcomes

Default candidate budgets are inputBytes=1048576, depth=128, nodes=100000 and
numberBytes=4096. A scalar root has depth zero; entering each array/object child
adds one. The node budget charges one for every Value plus one for each object
entry. Strings are bounded indirectly by input size. Limits are configurable
natural numbers, including zero; they require explicit boundary tests.

The result is either an AST or ParseError(kind, offset). Offsets are absolute
zero-based diagnostic byte positions within the operation input; end-of-input
may be reported as input length. This wire-v1 draft promises bounded positions,
not an exact offending byte or earliest failure. A token-start position or zero
can be a valid diagnostic. A future precise ErrorAt/prefix-failure contract must
be reviewed separately. Kinds
are syntax, utf8, limit and unsupported. utf8 is invalid document encoding. A limit
outcome makes no statement that the complete input is syntactically invalid.
Implementation fuel exhaustion is a limit, distinct from syntax. Timeout, crash,
missing executable or malformed oracle output are infrastructure failures in
the caller, not parser results. Precise error precedence is still a review item.

## Serialization and profiles

Serialization emits valid ASCII JSON by escaping every UTF-16 unit, keeps object
entry order and duplicates, and emits number tokens only after lexical validation.
The candidate output limit is 8388608 bytes. Invalid handcrafted number ASTs are
rejected. For this serializer API, ParseError.offset is the emitted output-byte
position, since the input is an AST rather than bytes; separating parser and
serializer error types is a human-review item. Whitespace and original escape
spelling cannot be reconstructed.

A strict scalar/unique-key profile is a separate validator. The binary64 profile,
FloatLib admission, cache, Rust refinement and production reporter are not part
of the bootstrap claim.

## Proof obligations

The independent relations must eventually describe arbitrary document membership
and semantics. Successful parser executions alone cannot define those relations.
The first local proofs concern cursor bounds and an independently specified
number grammar. Complete parser soundness/completeness, modeled costs, serializer
round trip, transport round trip and native API bindings remain separate roots.

Human review covers the types, grammar/semantic relations, budgets, theorem
statements, profiles and trust boundary. Review can revise this draft before
packets are frozen; contribution proofs cannot change frozen meaning to pass.
