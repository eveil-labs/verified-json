import VerifiedJson.String
import VerifiedJson.Transport

/-!
Focused executable API regressions. These observations are not proof roots and do
not establish general parser or codec correctness. Run the native test target.
-/

namespace VerifiedJson.ApiRegression

private def check (label : String) (condition : Bool) : IO Unit :=
  if condition then pure () else throw (IO.userError s!"API regression failed: {label}")

private def expectError {α : Type} (label : String) (result : Except ParseError α)
    (kind : ErrorKind) (offset : Nat) : IO Unit :=
  match result with
  | .error error => check label (error.kind == kind && error.offset == offset)
  | .ok _ => throw (IO.userError s!"API regression unexpectedly accepted: {label}")

private def expectString (label : String) (input : ByteArray) (start : Nat)
    (units : List UInt16) (next : Nat) : IO Unit :=
  match StringParser.parse input start with
  | .ok (actual, pos) => check label (actual == units && pos == next)
  | .error error => throw (IO.userError s!"API string regression refused {label}: {repr error}")

private def stringOffsets : IO Unit := do
  let invalid : List (ByteArray × Nat × Nat) := [
    (ByteArray.empty, 0, 0), (ByteArray.empty, 1, 0), (ByteArray.empty, 100000, 0),
    ("abc".toUTF8, 0, 0), ("abc".toUTF8, 3, 3), ("abc".toUTF8, 4, 3),
    ("abc".toUTF8, 1000000000000000000000000000000, 3),
    ("\"x\"".toUTF8, 1, 1), ("\"x\"".toUTF8, 3, 3), ("\"x\"".toUTF8, 4, 3),
    (" \"x\" ".toUTF8, 0, 0), (" \"x\" ".toUTF8, 5, 5), (" \"x\" ".toUTF8, 6, 5),
    ("\"é\"".toUTF8, 2, 2), ("\"é\"".toUTF8, 4, 4), ("\"é\"".toUTF8, 5, 4),
    ("\"".toUTF8, 0, 1), ("\"\\u".toUTF8, 0, 3)]
  for (input, start, offset) in invalid do
    expectError s!"string start {start}, size {input.size}"
      (StringParser.parse input start) .syntax offset
  expectString "root string" "\"x\"".toUTF8 0 [0x78] 3
  expectString "offset string" " \"x\" ".toUTF8 1 [0x78] 4
  expectString "raw UTF-8 string" "\"é\"".toUTF8 0 [0xE9] 4
  expectString "escaped surrogate" "\"\\uD800\"".toUTF8 0 [0xD800] 8
  expectError "raw surrogate UTF-8"
    (StringParser.parse (ByteArray.mk #[0x22, 0xED, 0xA0, 0x80, 0x22])) .utf8 1

private def invalidNumberFields : IO Unit := do
  let ascii := ["", "x", "01", "+1", "-01", "1.", "1e", "1e+", "--1", "1 2", "NaN"]
  let nonAscii := ["∞", "１", "١", "0é", "−1"]
  for (tokens, kind) in [(ascii, ErrorKind.syntax), (nonAscii, ErrorKind.unsupported)] do
    for token in tokens do
      let value := Value.number token
      let wrapped : List Value := [value, .array [value], .object [([0x61], value)],
        .array [.null, .object [([], .array [.number "0", value])]]]
      for ast in wrapped do
        expectError s!"transport number {repr token}" (Transport.encode ast) kind 0

private def validNumberFields : IO Unit := do
  -- Golden neutral frames preserve signs, fraction/exponent spelling and huge exponents.
  let cases : List (String × String) := [
    ("0", "030100000030"), ("-0", "03020000002d30"),
    ("1", "030100000031"), ("10", "03020000003130"),
    ("0.0", "0303000000302e30"), ("1e0", "0303000000316530"),
    ("1E+999", "030600000031452b393939"),
    ("0e-01", "030500000030652d3031"),
    ("1e400", "03050000003165343030"),
    ("-0.00e+001", "030a0000002d302e3030652b303031")]
  for (token, expected) in cases do
    match Transport.encode (.number token) with
    | .ok bytes => check s!"number frame {token}" (Transport.toHex bytes == expected)
    | .error error => throw (IO.userError s!"valid number refused {token}: {repr error}")
  -- This API has an output cap, not the parser's default 4,096-byte token cap.
  let longToken := String.ofList (List.replicate 4097 '1')
  match Transport.encode (.number longToken) 0 4102 with
  | .ok bytes => check "long grammatical token exact output cap" (bytes.size == 4102)
  | .error error => throw (IO.userError s!"long valid number refused: {repr error}")
  expectError "long grammatical token below output cap"
    (Transport.encode (.number longToken) 0 4101) .limit 0
  expectError "valid number zero output cap" (Transport.encode (.number "0") 0 0) .limit 0

/-- Execute the focused tests; an assertion failure is an IO error, never a PASS marker. -/
def run : IO Unit := do
  stringOffsets
  invalidNumberFields
  validNumberFields

end VerifiedJson.ApiRegression

def main : IO UInt32 := do
  VerifiedJson.ApiRegression.run
  IO.println "PASS_API_REGRESSIONS"
  return 0
