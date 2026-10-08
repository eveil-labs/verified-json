# Independent JSON document contract for human review

**Draft; semantic approval is pending.** Review [DocumentSpec.lean](../lean/VerifiedJson/DocumentSpec.lean), SHA-256 `ee1c73d10a6ff7daa28867c04c9f8b83821ba0044335742432b34ac7a345103e`. It imports only the existing wire types and independent number grammar. It contains no parser, token recognizer, serializer, transport, or candidate comparison call. The proposed definitions occupy the first part of the file; constructive witnesses and source proofs follow them.

Fresh Lean 4.35.0-rc4 compilation accepted this source and its proof bodies. Compilation does not approve the meaning of this specification or prove the current parser conforms to it. Independent replay, implication from the intended standard, determinism, and implementation refinement remain separate gates.

## Contract being proposed

The input domain is every finite ByteArray, including invalid UTF-8. `Document input value` is a declarative relation: one JSON value occupies the complete input, surrounded only by JSON whitespace. An invalid input has no related value. This is not an executable decision procedure or a new claim of parser total correctness.

The wire value keeps number lexemes, UTF-16 code units, member order and duplicate members. It does not preserve whitespace or escape spelling. Strings can therefore retain an escaped lone surrogate. A strict scalar/unique-key application profile remains a separate later contract. No numerical value, binary64 rounding, numeric range rejection or formatting policy is specified here.

The proposal uses strict UTF-8 for raw text, rejects an initial BOM, permits noncharacters/unassigned scalar values, retains lone escaped surrogates, and preserves duplicate names. BOM skipping and stricter scalar/key profiles can be added separately if desired.

## Review checklist

Record a decision on every item, including proposed edits. Approval should bind the exact source hash and the existing Spec/Grammar dependency hashes, rather than only this prose.

| Review item | Definition to inspect | Proposed interpretation |
| --- | --- | --- |
| Domain and numeric preservation | `Document`, `JsonValue.number`, existing `Grammar.NumberToken` | All finite bytes are representable as inputs; accepted number bytes equal the retained String's UTF-8 bytes. No machine numeric conversion. |
| UTF-8 boundaries | `Utf8Scalar`, `IsContinuation` | ASCII; C2–DF; E0–EF with E0/ED restrictions; F0–F4 with F0/F4 restrictions. Continuations are 80–BF. No overlong sequence, raw surrogate or code point above U+10FFFF. |
| Scalar meaning | `IsScalar`, `scalarToUtf16` | BMP scalar becomes one unit; supplementary scalar becomes the arithmetic high/low pair. No Unicode normalization. |
| Raw string characters | `RawAllowed`, `StringPiece.raw` | Exclude U+0000–001F, quote and backslash; slash and other scalar values remain allowed. |
| Simple escapes | `SimpleEscape`, `StringPiece.simple` | Inspect all eight input/output mappings, especially backspace/form feed versus the letters b/f. |
| Unicode escapes | `HexDigit`, `StringPiece.unicode` | Exactly four ASCII hexadecimal digits after lowercase u; case-insensitive hex letters; one resulting 16-bit unit, including a lone surrogate. |
| String boundaries | `StringContents`, `QuotedString` | Concatenate decoded units without rewriting them; require both quote delimiters; allow empty content. |
| Whitespace and literals | `IsWhitespace`, `Whitespace`, literal `JsonValue` constructors | Only space/tab/LF/CR; lowercase exact null/true/false; any value is legal at the top level. |
| Containers | `ArrayElements`, `Member`, `ObjectMembers`, array/object constructors | Correct brackets, colon, comma and optional surrounding whitespace. Every comma is followed by another actual item. No trailing comma or comments. |
| Object meaning | `ObjectMembers` and existing `Value.object` | Wire order and duplicates remain observable; keys are decoded unit sequences. No last-wins map conversion in this contract. |
| Consumption and BOM | `DocumentBytes` | Entire list equals leading whitespace, one value payload and trailing whitespace. No ignored suffix; no initial BOM exception. |
| Structural limits | `ShapeFits`, `ElementsFit`, `MembersFit`, `FitsLimits` | Root depth zero; child value depth increases by one; each Value and each object entry counts one node; keys are not additional Value nodes; number lexemes have their own byte limit. |

The numeric/Boolean/empty root has depth zero. An empty container fits a depth limit of zero; a container with a child Value requires depth at least one. These examples make the proposed *Value depth* convention precise; it is not an unstated container-count convention.

`FitsLimits` is a structural predicate, not a syntax predicate. Correct acceptance requires both `Document` and `FitsLimits`. Limits cover input bytes, Value depth, nodes and number-token bytes. This proposal does not add an output-size limit, string-size limit, operational timeout, fuel-success predicate or proof-build budget. Those remain separate explicit contracts.

## Independent references

[RFC 8259](https://www.rfc-editor.org/rfc/rfc8259.html#section-2) supplies the JSON grammar; sections 4–7 cover containers, numbers and strings. Section 8 discusses UTF-8, optional parser BOM handling and escaped lone surrogates. Keeping duplicates/order is this project's lossless wire representation, with later projections handling application policies.

[RFC 3629 section 4](https://www.rfc-editor.org/rfc/rfc3629.html#section-4) supplies the byte-range and boundary restrictions. [Unicode 17, chapter 3, §3.9](https://www.unicode.org/versions/Unicode17.0.0/core-spec/chapter-3/) describes scalar values and Unicode encoding forms. The proposal's Unicode arithmetic is restricted to scalar ranges and UTF-16 code units; no changing Unicode character-property table is imported.

These are references for human interpretation, not compiler inputs. The code was authored as mathematical relations rather than copied from a parser implementation or defined as its accepted outputs.

## Constructive evidence in the proposal

The source contains witnesses for null, an empty array, an empty string, raw A, escaped tab, a lone escaped high surrogate, and an ordered object with duplicate names. Concrete cent/euro/musical-symbol encodings exercise the two/three/four-byte cases; UTF-16 arithmetic is checked for the musical symbol. A general theorem shows every `Utf8Scalar` constructor denotes a scalar.

Negative source proofs exclude raw quote/control, surrogate/out-of-range scalar values, direct surrogate/above-maximum UTF-8 cases, and an overlong two-byte encoding. A whole-document theorem rejects empty input for every output Value. The negative scalar/encoding witnesses have exactly the scopes in their theorem signatures; they are not a proof of every malformed-input case in the running parser.

The optional structural relation has witnesses for an empty root array requiring one node at depth zero and one object entry with a null value requiring three total nodes. General structural-count uniqueness and monotonicity are not yet proved.

## Proposed J05/J06/J16 statements

These are statement proposals, not Lean declarations silently assumed true. `P` below means the exact public parser definition nominated and pinned by the subsequent packet; it cannot be replaced by an arbitrary function or an implementation-defined acceptance predicate.

**J05, soundness and public-success binding:** for all input bytes `b`, limits `L` and values `v`,

```text
P b L = ok v  →  Document b v ∧ FitsLimits b L v
```

Add public-result/consumption identity and offset bounds for the chosen API. The document relation already describes full consumption; a future prefix API needs a distinct relation.

**J06, completeness within the independently declared limits:** for all `b`, `L`, `v`,

```text
Document b v ∧ FitsLimits b L v  →  P b L = ok v
```

Before freezing this root, establish document interpretation uniqueness and validate that implementation budgets match the relational count/depth convention. A proof may not introduce “provided the implementation succeeds,” an arbitrary hidden resource premise, or a predicate defined by P as its completeness condition. If explicit work fuel is needed, define its independent cost model and a sufficient bound as a separate reviewed obligation.

**Diagnostic position decision for this draft:** the proposed public promise is
only an operation-relative, bounded diagnostic position. It does not promise the
exact offending byte or the earliest invalid prefix. A wrapper returning zero
for all error offsets satisfies this deliberately limited promise. If a precise
location is required, define an independent `ErrorAt`/prefix-failure relation,
including token starts, EOF, UTF-8 sequence starts and precedence, and add a
separate reviewed theorem. `J16ErrorOffsetBound` alone must never be described as
error-location correctness. No existing success or grammar obligation is changed.

**J16, results/errors and deployed API:** bind the exact public parser success values and root implementation identity to J05/J06. Define independently what syntax, UTF-8, budget and unsupported-profile outcomes mean. `Utf8Text` is available for the byte-encoding component, but its relation to document syntax and the proposed error policy still need proofs and review. A limit refusal may occur before a full syntax judgment, so it must not be advertised as proof that the input is invalid JSON.

Error offsets are operation-relative bytes: input offsets for parsing, emitted-output offsets for serialization. Public transport tags, compiled artifacts, trusted runtime primitives and cross-language adapters require separate J16 binding/review. None is proved by this declarative grammar.

**Exact proposed Lean type shapes:** the following is review text, not compiled declarations or proof assumptions. The final packet replaces the parameter P with the reviewed exact implementation identity and preserves its independently defined specification dependencies.

```lean
abbrev DraftParser := ByteArray → Limits → Except ParseError Value

def J05Statement (P : DraftParser) : Prop :=
  ∀ (b : ByteArray) (L : Limits) (v : Value),
    P b L = .ok v →
      VerifiedJson.DocumentSpec.Document b v ∧
        VerifiedJson.DocumentSpec.FitsLimits b L v

def J06Statement (P : DraftParser) : Prop :=
  ∀ (b : ByteArray) (L : Limits) (v : Value),
    VerifiedJson.DocumentSpec.Document b v ∧
      VerifiedJson.DocumentSpec.FitsLimits b L v → P b L = .ok v

def J16SyntaxRejection (P : DraftParser) : Prop :=
  ∀ (b : ByteArray) (L : Limits) (offset : Nat),
    P b L = .error ⟨.syntax, offset⟩ →
      ¬ ∃ v : Value, VerifiedJson.DocumentSpec.Document b v

def J16Utf8Rejection (P : DraftParser) : Prop :=
  ∀ (b : ByteArray) (L : Limits) (offset : Nat),
    P b L = .error ⟨.utf8, offset⟩ →
      ¬ VerifiedJson.DocumentSpec.Utf8Text b.toList

def J16ErrorOffsetBound (P : DraftParser) : Prop :=
  ∀ (b : ByteArray) (L : Limits) (error : ParseError),
    P b L = .error error → error.offset ≤ b.size

def J16PublicLogicalBinding (reference publicAPI : DraftParser) : Prop :=
  ∀ (b : ByteArray) (L : Limits), publicAPI b L = reference b L
```

The syntax/UTF-8 rejection statements are candidate policies to approve, not claims inferred merely from the error names. A concrete counterexample must be retained if the selected prototype violates them. The budget/unsupported result statements await independent prefix-budget and profile definitions; no vacuous placeholder theorem is proposed for those outcomes. Public logical binding does not certify a compiled binary, wire codec, compiler or runtime.

## Meaning still needing a human decision

The requested review is to confirm or edit the exact wire/profile choices, byte grammar, numeric-token relation and structural budget semantics. A successful Lean build cannot decide whether those definitions express the intended product. After human approval, maintainers freeze the accepted source/dependency identity, open the corresponding qualified proof packets, and prove implementation conformance without weakening this contract to fit the prototype.

The proposal has not changed any existing product definition or proof root. No Ready ticket, mathematical admission or release follows from its preparation.
