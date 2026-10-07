import VerifiedJson.Spec
import VerifiedJson.Grammar

namespace VerifiedJson.Number

open Grammar

structure Result where
  lexeme : String
  endPos : Nat
  deriving Repr, BEq

def isDigit (byte : UInt8) : Bool := decide (IsDigit byte)

def isNumberByte (byte : UInt8) : Bool :=
  isDigit byte || byte == 45 || byte == 43 || byte == 46 || byte == 101 || byte == 69

private def splitNegative (bytes : List UInt8) : Bool × List UInt8 :=
  match bytes with
  | [] => (false, [])
  | first :: rest => if first == 45 then (true, rest) else (false, bytes)

private def splitExponentSign (bytes : List UInt8) : ExponentSign × List UInt8 :=
  match bytes with
  | [] => (.absent, [])
  | first :: rest =>
    if first == 43 then (.plus, rest)
    else if first == 45 then (.minus, rest)
    else (.absent, bytes)

/-- Propose a grammatical decomposition; the independent contract checks it below. -/
def splitParts (bytes : List UInt8) : NumberParts := Id.run do
  let (negative, unsigned) := splitNegative bytes
  let integer := unsigned.takeWhile isDigit
  let afterInteger := unsigned.dropWhile isDigit
  let (fraction, afterFraction) := match afterInteger with
    | [] => (none, [])
    | first :: rest =>
      if first == 46 then
        (some (rest.takeWhile isDigit), rest.dropWhile isDigit)
      else (none, afterInteger)
  let exponent := match afterFraction with
    | [] => none
    | first :: rest =>
      if first == 101 || first == 69 then
        let (sign, digits) := splitExponentSign rest
        some { uppercase := first == 69, sign, digits }
      else none
  return { negative, integer, fraction, exponent }

/-- Accept only a decomposition satisfying the independent grammar and exact bytes. -/
def checkToken (bytes : List UInt8) : Option NumberParts :=
  let parts := splitParts bytes
  if parts.Valid ∧ parts.encode = bytes then some parts else none

theorem checkToken_sound (bytes : List UInt8) (parts : NumberParts)
    (h : checkToken bytes = some parts) : NumberToken bytes := by
  unfold checkToken at h
  dsimp only at h
  split at h
  · cases h
    rename_i hv
    exact ⟨splitParts bytes, hv.1, hv.2⟩
  · contradiction

/-- Whole-lexeme validation has no parser's default number-size budget. -/
def isValidLexeme (lexeme : String) : Bool :=
  (checkToken lexeme.toUTF8.toList).isSome

theorem isValidLexeme_sound (lexeme : String) (h : isValidLexeme lexeme = true) :
    NumberToken lexeme.toUTF8.toList := by
  unfold isValidLexeme at h
  simp only [String.toUTF8_eq_toByteArray] at h ⊢
  cases hc : checkToken lexeme.toByteArray.toList with
  | none => simp [hc] at h
  | some parts => exact checkToken_sound _ _ hc

/-- Scan at most the explicit fuel, consuming only number-related ASCII bytes. -/
def scanEnd (input : ByteArray) : Nat → Nat → Nat
  | pos, 0 => pos
  | pos, fuel + 1 =>
    if h : pos < input.size then
      if isNumberByte (input.get pos h) then scanEnd input (pos + 1) fuel else pos
    else pos

theorem scanEnd_bounds (input : ByteArray) (fuel pos : Nat) (h : pos ≤ input.size) :
    pos ≤ scanEnd input pos fuel ∧ scanEnd input pos fuel ≤ input.size := by
  induction fuel generalizing pos with
  | zero => simp [scanEnd, h]
  | succ fuel ih =>
    simp only [scanEnd]
    split
    · split
      · have next := ih (pos + 1) (by omega)
        omega
      · exact ⟨Nat.le_refl _, h⟩
    · exact ⟨Nat.le_refl _, h⟩

def parse (input : ByteArray) (start : Nat := 0) (limit : Nat := 4096) :
    Except ParseError Result :=
  if input.size < start then .error ⟨.syntax, input.size⟩
  else
    let stop := scanEnd input start (input.size - start)
    let token := input.extract start stop
    if limit < token.size then .error ⟨.limit, start⟩
    else
      match checkToken token.toList with
      | none => .error ⟨.syntax, start⟩
      | some _ =>
        match String.fromUTF8? token with
        | none => .error ⟨.utf8, start⟩
        | some lexeme => .ok { lexeme, endPos := stop }

private theorem decoded_bytes (bytes : ByteArray) (text : String)
    (h : String.fromUTF8? bytes = some text) : text.toUTF8 = bytes := by
  unfold String.fromUTF8? at h
  split at h
  · cases h
    rfl
  · contradiction

/-- Every successful parser result is an independently grammatical number token. -/
theorem parse_sound (input : ByteArray) (start limit : Nat) (result : Result)
    (h : parse input start limit = .ok result) : NumberToken result.lexeme.toUTF8.toList := by
  unfold parse at h
  split at h
  · contradiction
  · dsimp only at h
    split at h
    · contradiction
    · split at h
      · contradiction
      · split at h
        · contradiction
        · cases h
          rw [decoded_bytes _ _ (by assumption)]
          apply checkToken_sound
          assumption

/-- Successful number scans stay within the input and never move backwards. -/
theorem parse_bounds (input : ByteArray) (start limit : Nat) (result : Result)
    (h : parse input start limit = .ok result) :
    start ≤ result.endPos ∧ result.endPos ≤ input.size := by
  unfold parse at h
  split at h
  · contradiction
  · dsimp only at h
    split at h
    · contradiction
    · split at h
      · contradiction
      · split at h
        · contradiction
        · cases h
          exact scanEnd_bounds input _ start (by omega)

/-- The returned token bytes are exactly its consumed input span. -/
theorem parse_span (input : ByteArray) (start limit : Nat) (result : Result)
    (h : parse input start limit = .ok result) :
    result.lexeme.toUTF8 = input.extract start result.endPos := by
  unfold parse at h
  split at h
  · contradiction
  · dsimp only at h
    split at h
    · contradiction
    · split at h
      · contradiction
      · split at h
        · contradiction
        · cases h
          exact decoded_bytes _ _ (by assumption)

/-- A successful result respects the caller's number-token byte budget. -/
theorem parse_limit (input : ByteArray) (start limit : Nat) (result : Result)
    (h : parse input start limit = .ok result) : result.lexeme.toUTF8.size ≤ limit := by
  unfold parse at h
  split at h
  · contradiction
  · dsimp only at h
    split at h
    · contradiction
    · split at h
      · contradiction
      · split at h
        · contradiction
        · cases h
          rw [decoded_bytes _ _ (by assumption)]
          omega

/-- The zero token provides an executable positive witness using kernel reduction. -/
theorem zero_lexeme_valid : isValidLexeme "0" = true := by
  decide +kernel

/-- An exponent without digits is rejected by the complete-token recognizer. -/
theorem incomplete_exponent_rejected : isValidLexeme "1e" = false := by
  decide +kernel

end VerifiedJson.Number
