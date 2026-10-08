import VerifiedJson.Spec

namespace VerifiedJson.StringParser

private def byteAt (input : ByteArray) (pos : Nat) : Option Nat :=
  (input[pos]?).map UInt8.toNat

private def fail (kind : ErrorKind) (offset : Nat) : Except ParseError α :=
  .error { kind, offset }

private def hexValue (b : Nat) : Option Nat :=
  if 48 ≤ b && b ≤ 57 then some (b - 48)
  else if 65 ≤ b && b ≤ 70 then some (b - 55)
  else if 97 ≤ b && b ≤ 102 then some (b - 87)
  else none

private def readHex (input : ByteArray) : Nat → Nat → Nat → Except ParseError Nat
  | 0, _, acc => .ok acc
  | count + 1, pos, acc => do
    let some b := byteAt input pos | fail .syntax pos
    let some h := hexValue b | fail .syntax pos
    readHex input count (pos + 1) (acc * 16 + h)

private def continuation (input : ByteArray) (pos : Nat) (start : Nat) : Except ParseError Nat := do
  let some b := byteAt input pos | fail .utf8 start
  if 128 ≤ b && b ≤ 191 then .ok (b - 128) else fail .utf8 pos

/-- UTF-16 encoding of a valid Unicode scalar. Callers validate the scalar range. -/
def scalarUnits (scalar : Nat) : List UInt16 :=
  if scalar ≤ 65535 then [UInt16.ofNat scalar]
  else
    let shifted := scalar - 65536
    [UInt16.ofNat (55296 + shifted / 1024), UInt16.ofNat (56320 + shifted % 1024)]

/-- Decode one raw non-ASCII UTF-8 scalar. Overlong encodings, surrogate scalars,
and values greater than U+10FFFF are rejected. -/
private def rawScalar (input : ByteArray) (start : Nat) : Except ParseError (List UInt16 × Nat) := do
  let some lead := byteAt input start | fail .utf8 start
  if lead < 194 then fail .utf8 start
  else if lead ≤ 223 then
    let b1 ← continuation input (start + 1) start
    let scalar := (lead - 192) * 64 + b1
    .ok (scalarUnits scalar, start + 2)
  else if lead ≤ 239 then
    let b1 ← continuation input (start + 1) start
    let b2 ← continuation input (start + 2) start
    let scalar := (lead - 224) * 4096 + b1 * 64 + b2
    if scalar < 2048 || (55296 ≤ scalar && scalar ≤ 57343) then fail .utf8 start
    else .ok (scalarUnits scalar, start + 3)
  else if lead ≤ 244 then
    let b1 ← continuation input (start + 1) start
    let b2 ← continuation input (start + 2) start
    let b3 ← continuation input (start + 3) start
    let scalar := (lead - 240) * 262144 + b1 * 4096 + b2 * 64 + b3
    if scalar < 65536 || scalar > 1114111 then fail .utf8 start
    else .ok (scalarUnits scalar, start + 4)
  else fail .utf8 start

private def escaped (input : ByteArray) (slash : Nat) : Except ParseError (UInt16 × Nat) := do
  let some b := byteAt input (slash + 1) | fail .syntax (slash + 1)
  if b == 117 then
    let unit ← readHex input 4 (slash + 2) 0
    .ok (UInt16.ofNat unit, slash + 6)
  else
    let unit := match b with
      | 34 => some 34 | 92 => some 92 | 47 => some 47
      | 98 => some 8 | 102 => some 12 | 110 => some 10
      | 114 => some 13 | 116 => some 9 | _ => none
    let some unit := unit | fail .syntax (slash + 1)
    .ok (UInt16.ofNat unit, slash + 2)

private def loop (input : ByteArray) : Nat → Nat → List UInt16 → Except ParseError (List UInt16 × Nat)
  | 0, pos, _ => fail .limit pos
  | fuel + 1, pos, reversed => do
    let some b := byteAt input pos | fail .syntax pos
    if b == 34 then .ok (reversed.reverse, pos + 1)
    else if b == 92 then
      let (unit, next) ← escaped input pos
      loop input fuel next (unit :: reversed)
    else if b < 32 then fail .syntax pos
    else if b < 128 then loop input fuel (pos + 1) (UInt16.ofNat b :: reversed)
    else
      let (units, next) ← rawScalar input pos
      loop input fuel next (units.reverse ++ reversed)

/-- Parse a JSON string beginning at an absolute byte offset. The closing quote is consumed.
Escaped UTF-16 units are retained even when they are unpaired surrogates.
A starting offset beyond the input is rejected at the input length. -/
def parse (input : ByteArray) (start : Nat := 0) : Except ParseError (List UInt16 × Nat) := do
  if input.size < start then fail .syntax input.size
  else if byteAt input start != some 34 then fail .syntax start
  else loop input (input.size + 1) (start + 1) []

/-- A caller-supplied start beyond the input reports the input boundary. -/
theorem parse_past_end (input : ByteArray) (start : Nat) (h : input.size < start) :
    parse input start = .error ⟨.syntax, input.size⟩ := by
  simp [parse, h, fail]

/-- Valid BMP scalars have the independently specified single-unit UTF-16 encoding. -/
theorem scalarUnits_bmp (scalar : Nat) (h : scalar ≤ 65535) :
    scalarUnits scalar = [UInt16.ofNat scalar] := by
  simp [scalarUnits, h]

end VerifiedJson.StringParser
