import Std

/-!
Independent ASCII JSON-number grammar, following RFC 8259 section 6. The relation
uses grammatical components and never calls the scanner or recognizer.
-/

namespace VerifiedJson.Grammar

def IsDigit (byte : UInt8) : Prop := 48 ≤ byte.toNat ∧ byte.toNat ≤ 57

def IsNonzeroDigit (byte : UInt8) : Prop := 49 ≤ byte.toNat ∧ byte.toNat ≤ 57

def AllDigits : List UInt8 → Prop
  | [] => True
  | byte :: rest => IsDigit byte ∧ AllDigits rest

instance (byte : UInt8) : Decidable (IsDigit byte) :=
  inferInstanceAs (Decidable (48 ≤ byte.toNat ∧ byte.toNat ≤ 57))

instance (byte : UInt8) : Decidable (IsNonzeroDigit byte) :=
  inferInstanceAs (Decidable (49 ≤ byte.toNat ∧ byte.toNat ≤ 57))

def allDigitsDecidable : (bytes : List UInt8) → Decidable (AllDigits bytes)
  | [] => isTrue True.intro
  | byte :: rest =>
    letI := allDigitsDecidable rest
    inferInstanceAs (Decidable (IsDigit byte ∧ AllDigits rest))

instance (bytes : List UInt8) : Decidable (AllDigits bytes) := allDigitsDecidable bytes

def IntegerPart : List UInt8 → Prop
  | [] => False
  | first :: rest =>
    (first = 48 ∧ rest = []) ∨ (IsNonzeroDigit first ∧ AllDigits rest)

instance (bytes : List UInt8) : Decidable (IntegerPart bytes) := by
  cases bytes with
  | nil => exact isFalse (fun h => h)
  | cons first rest =>
    exact inferInstanceAs
      (Decidable ((first = 48 ∧ rest = []) ∨ (IsNonzeroDigit first ∧ AllDigits rest)))

def NonemptyDigits (bytes : List UInt8) : Prop := bytes ≠ [] ∧ AllDigits bytes

instance (bytes : List UInt8) : Decidable (NonemptyDigits bytes) :=
  inferInstanceAs (Decidable (bytes ≠ [] ∧ AllDigits bytes))

def OptionalDigits : Option (List UInt8) → Prop
  | none => True
  | some bytes => NonemptyDigits bytes

instance (bytes : Option (List UInt8)) : Decidable (OptionalDigits bytes) := by
  cases bytes with
  | none => exact isTrue True.intro
  | some bytes => exact inferInstanceAs (Decidable (NonemptyDigits bytes))

inductive ExponentSign where
  | absent
  | plus
  | minus
  deriving Repr, BEq, Inhabited

def ExponentSign.encode : ExponentSign → List UInt8
  | .absent => []
  | .plus => [43]
  | .minus => [45]

structure Exponent where
  uppercase : Bool
  sign : ExponentSign
  digits : List UInt8
  deriving Repr, BEq

structure NumberParts where
  negative : Bool
  integer : List UInt8
  fraction : Option (List UInt8)
  exponent : Option Exponent
  deriving Repr, BEq

def NumberParts.encode (parts : NumberParts) : List UInt8 :=
  (if parts.negative then [45] else []) ++ parts.integer ++
    (match parts.fraction with
     | none => []
     | some digits => 46 :: digits) ++
    (match parts.exponent with
     | none => []
     | some exponent =>
       (if exponent.uppercase then 69 else 101) ::
         (exponent.sign.encode ++ exponent.digits))

def NumberParts.Valid (parts : NumberParts) : Prop :=
  IntegerPart parts.integer ∧ OptionalDigits parts.fraction ∧
    OptionalDigits (parts.exponent.map (·.digits))

instance (parts : NumberParts) : Decidable parts.Valid :=
  inferInstanceAs (Decidable (IntegerPart parts.integer ∧ OptionalDigits parts.fraction ∧
    OptionalDigits (parts.exponent.map (·.digits))))

/-- A grammatical decomposition, independent of any implementation. -/
def NumberToken (bytes : List UInt8) : Prop :=
  ∃ parts : NumberParts, parts.Valid ∧ parts.encode = bytes

/-- The grammar is inhabited by the single-digit zero token. -/
theorem zero_numberToken : NumberToken [48] := by
  refine ⟨⟨false, [48], none, none⟩, ?_, ?_⟩
  · decide
  · rfl

/-- Exponent markers alone are not an integer component. -/
theorem exponentMarker_not_integer : ¬ IntegerPart [101] := by
  decide

end VerifiedJson.Grammar
