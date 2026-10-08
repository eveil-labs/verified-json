import VerifiedJson.Spec
import VerifiedJson.Number

namespace VerifiedJson.Transport

/-- Candidate transport cap; this is independent of JSON syntax. -/
def maxResponseBytes : Nat := 32 * 1024 * 1024

private def failLimit : Except ParseError α := .error ⟨.limit, 0⟩

private def append (a b : ByteArray) (cap : Nat) : Except ParseError ByteArray :=
  if a.size + b.size ≤ cap then .ok (a ++ b) else failLimit

private def count (n : Nat) : Except ParseError ByteArray :=
  if n < 4294967296 then
    .ok (ByteArray.mk #[UInt8.ofNat n, UInt8.ofNat (n / 256),
      UInt8.ofNat (n / 65536), UInt8.ofNat (n / 16777216)])
  else failLimit

private def units (xs : List UInt16) (cap : Nat) : Except ParseError ByteArray := do
  let header ← count xs.length
  if 4 + 2 * xs.length > cap then failLimit else
    return xs.foldl (fun acc u => acc.push (UInt8.ofNat u.toNat)
      |>.push (UInt8.ofNat (u.toNat / 256))) header

private def encodeFuel (fuel : Nat) (v : Value) (cap : Nat) :
    Except ParseError ByteArray := do
  match fuel with
  | 0 => failLimit
  | fuel + 1 =>
    match v with
    | .null => if cap ≥ 1 then return ByteArray.mk #[0] else failLimit
    | .bool b => if cap ≥ 1 then return ByteArray.mk #[if b then 2 else 1] else failLimit
    | .number s =>
      let bytes := s.toUTF8
      if bytes.data.any (fun b => b.toNat > 127) then
        .error ⟨.unsupported, 0⟩
      else if !Number.isValidLexeme s then
        .error ⟨.syntax, 0⟩
      else
        let header ← count bytes.size
        let tagged ← append (ByteArray.mk #[3]) header cap
        append tagged bytes cap
    | .str s =>
      let payload ← units s cap
      append (ByteArray.mk #[4]) payload cap
    | .array xs =>
      let header ← count xs.length
      let tagged ← append (ByteArray.mk #[5]) header cap
      xs.foldlM (fun acc child => do
        let bytes ← encodeFuel fuel child cap
        append acc bytes cap) tagged
    | .object xs =>
      let header ← count xs.length
      let tagged ← append (ByteArray.mk #[6]) header cap
      xs.foldlM (fun acc (key, child) => do
        let keyBytes ← units key cap
        let withKey ← append acc keyBytes cap
        let childBytes ← encodeFuel fuel child cap
        append withKey childBytes cap) tagged

/-- Prototype encoding, with depth and output bounds. Invalid ASCII number lexemes
are rejected as syntax; non-ASCII number fields retain the unsupported outcome.
Codec refinement is open. -/
def encode (v : Value) (depth : Nat := 128) (cap : Nat := maxResponseBytes) :
    Except ParseError ByteArray := encodeFuel (depth + 1) v cap

private def hexChar (n : Nat) : Char :=
  Char.ofNat (if n < 10 then 48 + n else 87 + n)

def toHex (bytes : ByteArray) : String :=
  String.ofList (bytes.data.toList.flatMap fun b =>
    [hexChar (b.toNat / 16), hexChar (b.toNat % 16)])

private def digit (c : Char) : Option Nat :=
  let n := c.toNat
  if 48 ≤ n && n ≤ 57 then some (n - 48)
  else if 65 ≤ n && n ≤ 70 then some (n - 55)
  else if 97 ≤ n && n ≤ 102 then some (n - 87)
  else none

private def fromDigits : List Char → ByteArray → Except String ByteArray
  | [], acc => .ok acc
  | a :: b :: rest, acc =>
    match digit a, digit b with
    | some x, some y => fromDigits rest (acc.push (UInt8.ofNat (16 * x + y)))
    | _, _ => .error "invalid hex digit"
  | [_], _ => .error "odd hex length"

def fromHex (s : String) : Except String ByteArray := fromDigits s.toList ByteArray.empty

end VerifiedJson.Transport
