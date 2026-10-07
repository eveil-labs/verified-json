# FloatLib dependency admission

Status: investigated, **NOT_ADMITTED**. The JSON core currently imports no FloatLib or Mathlib modules and makes no binary64 conversion claim. A bounded source/import probe found relevant upstream decimal conversion contracts and one RC-compatible status module, but did not qualify the numeric conversion dependency.

## Exact candidate source

- Repository: [lean-dojo/FloatLib](https://github.com/lean-dojo/FloatLib).
- Observed source revision: [`7fc753899afed9562018fe09f336403b179eedbd`](https://github.com/lean-dojo/FloatLib/commit/7fc753899afed9562018fe09f336403b179eedbd), 2026-10-07T05:18:33Z.
- Git source tree: `169d490f54a3401a63b5a4f099d7e9f04c152868`.
- License: [MIT](https://github.com/lean-dojo/FloatLib/blob/7fc753899afed9562018fe09f336403b179eedbd/LICENSE). Any later vendored slice retains the license, copyright and exact upstream provenance.
- Upstream Lean selector: `leanprover/lean4:v4.34.0`.
- Upstream package sets `fixedToolchain := true` and requires Mathlib `v4.34.0`; its lock records Mathlib revision `5ed2965256430c3649e86755f9576b54eca72435`. [Package source](https://github.com/lean-dojo/FloatLib/blob/7fc753899afed9562018fe09f336403b179eedbd/lakefile.lean), [lock](https://github.com/lean-dojo/FloatLib/blob/7fc753899afed9562018fe09f336403b179eedbd/lake-manifest.json).

These are candidate identities, not a moving dependency selector. A future admission packet must bind the entire selected source/proof/runtime closure and the actual project compiler identity. The project compiler remains `leanprover/lean4:v4.35.0-rc4`; importing FloatLib must not silently downgrade it to upstream's selector.

## Useful entrypoints and proof scope

The smallest caller-facing entrypoint identified for decimal text conversion is `FloatLib.Floats.Formats.BinaryInterchange.Conversion.Text.BoundedParsing`. It exposes `Model.parse` with nearest-even rounding by default, optional byte/exponent limits and optional complete IEEE exception status. The generic `FloatLib` or `ExecFloat` umbrella imports are unnecessary for an initial JSON-number bridge. This is the smallest relevant entrypoint found in this probe, not a proved globally minimal transitive import closure. [Bounded parsing source](https://github.com/lean-dojo/FloatLib/blob/7fc753899afed9562018fe09f336403b179eedbd/FloatLib/Floats/Formats/BinaryInterchange/Conversion/Text/BoundedParsing.lean).

Upstream text conversion supports more spellings than JSON, including non-JSON special/radix forms and optional edge whitespace. The bridge must accept only already validated complete JSON number tokens, independently relate them to an exact signed decimal datum and retain an explicit negative-zero policy. Enabling FloatLib parsing cannot redefine the JSON grammar.

Relevant source contracts go beyond formatter round trips:

| Import / declaration | Useful property | Limit of that property |
| --- | --- | --- |
| `Conversion.Text.Parsing`: `convertDecimalTextExact` and `convertDecimalText` | Converts a signed exact decimal datum into a binary value plus exception flags. The practical implementation clamps extreme exponents. | A runtime definition alone does not establish its independent numerical meaning. |
| `Conversion.Text.ExponentClamp`: `convertDecimalText_eq_exact` | The practical clamp agrees with the exact reference on the complete outcome, for every exact decimal input and selected rounding mode. | The reference rounder and flag policy still need their own qualified contracts and JSON bridge. |
| `Conversion.Text.Roundtrip`: `toReal_parse_decimal_nearestEven` | Successfully read and parsed decimal input with a finite result has the nearest-even rounded real value of the exact decimal datum. The input need not have come from a formatter. | Its premises include successful decimal recognition/parsing and finite output; equality of real values alone does not establish signed-zero bits, tie-word policy or overflow outcomes. |
| `Conversion.Text.Roundtrip`: `parse_formatDecimal_of_isFinite` | A finite encoded value round-trips through its exact decimal formatter, including the word-level zero cases addressed there. | This generated-string theorem is not arbitrary JSON-number correctness or shortest-decimal printing. |

Sources: [runtime parsing](https://github.com/lean-dojo/FloatLib/blob/7fc753899afed9562018fe09f336403b179eedbd/FloatLib/Floats/Formats/BinaryInterchange/Conversion/Text/Parsing.lean), [clamp agreement](https://github.com/lean-dojo/FloatLib/blob/7fc753899afed9562018fe09f336403b179eedbd/FloatLib/Floats/Formats/BinaryInterchange/Conversion/Text/ExponentClamp.lean), [decimal input and round-trip theorems](https://github.com/lean-dojo/FloatLib/blob/7fc753899afed9562018fe09f336403b179eedbd/FloatLib/Floats/Formats/BinaryInterchange/Conversion/Text/Roundtrip.lean).

The project numeric contract must specify the complete binary64 word, signed zero, nearest-even ties, subnormal/underflow behavior, overflow handling and reported range outcome. It must connect the actual public API and compiled oracle to that contract. Finite real-valued equality alone is insufficient.

## Actual bounded probe

The probe used exact Lean `v4.35.0-rc4` on Darwin arm64 in disposable central WORK, with a private dependency-free Lake description. It did not run upstream's package setup, install Mathlib, fetch a framework cache or change the product dependency configuration. Fourteen selected upstream Lean files totaling 111,371 bytes were read at the pinned revision and verified against the API tree's Git blob identities; their SHA-256 identities are retained in the private source record.

| Unmodified upstream target | Observed result |
| --- | --- |
| `FloatLib.Numerics.IEEEStatus` | Compiler exit 0, fresh `.olean`, shared verdict **accept**, no warnings. Source SHA-256 `ef7cd01cf97e10c11adf145f8f15225736a7b1f3e22057462ad7f9bc052aceb6`. This checks a small status-record module, not decimal conversion. |
| `FloatLib.Numerics.Exact.RadixText.Runtime` | Compiler exit 1, no fresh artifact, shared verdict **INFRA** because the import `Mathlib.Data.Nat.Digits.Defs` was unavailable. The module body was not judged. Source SHA-256 `b94b5362f7fa9b0a3b30250664cbb15ba34b2f4c6651b90ca8b95cb561915ed3`. |

The decimal foundation also imports `FloatLib.Numerics.Exact.Dyadic.Basic`, which directly imports `Mathlib.Data.Rat.Cast.Order`. Both dependencies lie on the required conversion path. This is a concrete missing selected dependency closure and declared toolchain mismatch; it is not evidence that FloatLib's numeric proofs are false or that RC4 necessarily cannot support a reviewed port. [Radix runtime](https://github.com/lean-dojo/FloatLib/blob/7fc753899afed9562018fe09f336403b179eedbd/FloatLib/Numerics/Exact/RadixText/Runtime.lean), [dyadic foundation](https://github.com/lean-dojo/FloatLib/blob/7fc753899afed9562018fe09f336403b179eedbd/FloatLib/Numerics/Exact/Dyadic/Basic.lean).

A full source-archive request hit a conservative 64 MiB download cap before completion and was not extracted. The probe switched to small pinned source files instead of increasing the download or fetching Mathlib. No claim is made about the complete archive's size or why it exceeded the cap. No compatibility or numerical patch was applied.

## Next bounded admission work

1. Review the signed-decimal-to-binary64 contract and JSON-token bridge independently. Identify exact theorem roots and proof/runtime imports; do not enable numeric compatibility before the complete outcomes are covered.
2. Prepare a reviewed Mathlib source/toolchain closure compatible with the project's exact RC, within an explicit disk/build budget. Existing Lean 4.34 compiled artifacts cannot simply be reused under RC4. Keep the stable qualification lane separate.
3. Measure the actual transitive closure for BoundedParsing and the required numerical proofs. Prefer source-preserving module splits if unnecessary formatting, hex or configured-backend imports dominate.
4. Candidate small upstream changes include separating the radix scanner from its Mathlib-dependent digit printer and separating arbitrary-decimal semantics from formatting/hex round-trip proofs. Such changes must preserve existing definition bodies and statements; they still do not remove the dyadic/rational proof dependency by themselves. This is a proposal, not an applied shim or admitted patch.
5. Rebuild the selected closure, audit transitive axioms/runtime substitutions, replay through the qualified kernels, check complete binary64 API outcomes and run signed-zero/tie/subnormal/overflow/extreme-exponent fixtures. Unsupported replay or missing build inputs remain INFRA.

The current exact-token JSON parser remains useful while this admission work is pending. The status leaf's successful build does not make the numerical dependency Ready.
