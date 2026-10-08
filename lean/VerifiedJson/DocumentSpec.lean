import VerifiedJson.Spec
import VerifiedJson.Grammar

/-!
PROPOSAL FOR HUMAN SEMANTIC REVIEW. An independent byte-to-wire-value relation,
with an optional structural budget relation. No implementation is imported.
RFC 8259 sections 2-8 and RFC 3629 section 4 are the external grammar references.
-/

set_option autoImplicit false

namespace VerifiedJson.DocumentSpec

def IsScalar (cp : Nat) : Prop :=
  cp ≤ 0x10FFFF ∧ ¬ (0xD800 ≤ cp ∧ cp ≤ 0xDFFF)

def IsContinuation (byte : UInt8) : Prop :=
  0x80 ≤ byte.toNat ∧ byte.toNat ≤ 0xBF

/-- Shortest UTF-8 encodings, including the E0/ED/F0/F4 boundary restrictions. -/
inductive Utf8Scalar : List UInt8 → Nat → Prop where
  | one (a : UInt8) (ha : a.toNat ≤ 0x7F) : Utf8Scalar [a] a.toNat
  | two (a b : UInt8)
      (ha : 0xC2 ≤ a.toNat ∧ a.toNat ≤ 0xDF) (hb : IsContinuation b) :
      Utf8Scalar [a, b] ((a.toNat - 0xC0) * 64 + (b.toNat - 0x80))
  | three (a b c : UInt8)
      (ha : 0xE0 ≤ a.toNat ∧ a.toNat ≤ 0xEF)
      (hb : IsContinuation b) (hc : IsContinuation c)
      (shortest : a.toNat = 0xE0 → 0xA0 ≤ b.toNat)
      (noSurrogate : a.toNat = 0xED → b.toNat ≤ 0x9F) :
      Utf8Scalar [a, b, c]
        ((a.toNat - 0xE0) * 4096 + (b.toNat - 0x80) * 64 + (c.toNat - 0x80))
  | four (a b c d : UInt8)
      (ha : 0xF0 ≤ a.toNat ∧ a.toNat ≤ 0xF4)
      (hb : IsContinuation b) (hc : IsContinuation c) (hd : IsContinuation d)
      (shortest : a.toNat = 0xF0 → 0x90 ≤ b.toNat)
      (maximum : a.toNat = 0xF4 → b.toNat ≤ 0x8F) :
      Utf8Scalar [a, b, c, d]
        ((a.toNat - 0xF0) * 262144 + (b.toNat - 0x80) * 4096 +
          (c.toNat - 0x80) * 64 + (d.toNat - 0x80))

/-- UTF-8 validity of a complete byte sequence, independent of JSON syntax. -/
inductive Utf8Text : List UInt8 → Prop where
  | nil : Utf8Text []
  | cons {head tail : List UInt8} {cp : Nat}
      (scalar : Utf8Scalar head cp) (following : Utf8Text tail) :
      Utf8Text (head ++ tail)

/-- Exact UTF-16 mathematics; the caller's scalar predicate excludes surrogate inputs. -/
def scalarToUtf16 (cp : Nat) : List UInt16 :=
  if cp < 0x10000 then [UInt16.ofNat cp]
  else
    [UInt16.ofNat (0xD800 + (cp - 0x10000) / 1024),
     UInt16.ofNat (0xDC00 + (cp - 0x10000) % 1024)]

def RawAllowed (cp : Nat) : Prop := 0x20 ≤ cp ∧ cp ≠ 0x22 ∧ cp ≠ 0x5C

def SimpleEscape (code : UInt8) (unit : UInt16) : Prop :=
  (code = 0x22 ∧ unit = 0x22) ∨ (code = 0x5C ∧ unit = 0x5C) ∨
  (code = 0x2F ∧ unit = 0x2F) ∨ (code = 0x62 ∧ unit = 0x08) ∨
  (code = 0x66 ∧ unit = 0x0C) ∨ (code = 0x6E ∧ unit = 0x0A) ∨
  (code = 0x72 ∧ unit = 0x0D) ∨ (code = 0x74 ∧ unit = 0x09)

def HexDigit (byte : UInt8) (value : Nat) : Prop :=
  (0x30 ≤ byte.toNat ∧ byte.toNat ≤ 0x39 ∧ value = byte.toNat - 0x30) ∨
  (0x41 ≤ byte.toNat ∧ byte.toNat ≤ 0x46 ∧ value = byte.toNat - 0x41 + 10) ∨
  (0x61 ≤ byte.toNat ∧ byte.toNat ≤ 0x66 ∧ value = byte.toNat - 0x61 + 10)

inductive StringPiece : List UInt8 → List UInt16 → Prop where
  | raw {bytes : List UInt8} {cp : Nat}
      (encoding : Utf8Scalar bytes cp) (scalar : IsScalar cp) (allowed : RawAllowed cp) :
      StringPiece bytes (scalarToUtf16 cp)
  | simple (code : UInt8) (unit : UInt16) (meaning : SimpleEscape code unit) :
      StringPiece [0x5C, code] [unit]
  | unicode (a b c d : UInt8) (x y z w : Nat)
      (ha : HexDigit a x) (hb : HexDigit b y) (hc : HexDigit c z) (hd : HexDigit d w) :
      StringPiece [0x5C, 0x75, a, b, c, d]
        [UInt16.ofNat (4096 * x + 256 * y + 16 * z + w)]

inductive StringContents : List UInt8 → List UInt16 → Prop where
  | nil : StringContents [] []
  | cons {head tail : List UInt8} {units rest : List UInt16}
      (piece : StringPiece head units) (following : StringContents tail rest) :
      StringContents (head ++ tail) (units ++ rest)

inductive QuotedString : List UInt8 → List UInt16 → Prop where
  | quoted {body : List UInt8} {units : List UInt16} (content : StringContents body units) :
      QuotedString (0x22 :: body ++ [0x22]) units

def IsWhitespace (byte : UInt8) : Prop :=
  byte = 0x20 ∨ byte = 0x09 ∨ byte = 0x0A ∨ byte = 0x0D

inductive Whitespace : List UInt8 → Prop where
  | nil : Whitespace []
  | cons {byte : UInt8} {rest : List UInt8}
      (allowed : IsWhitespace byte) (following : Whitespace rest) :
      Whitespace (byte :: rest)

mutual
  inductive JsonValue : List UInt8 → Value → Prop where
    | null : JsonValue [0x6E, 0x75, 0x6C, 0x6C] .null
    | boolTrue : JsonValue [0x74, 0x72, 0x75, 0x65] (.bool true)
    | boolFalse : JsonValue [0x66, 0x61, 0x6C, 0x73, 0x65] (.bool false)
    | number (lexeme : String) (grammatical : Grammar.NumberToken lexeme.toUTF8.toList) :
        JsonValue lexeme.toUTF8.toList (.number lexeme)
    | str {bytes : List UInt8} {units : List UInt16} (grammatical : QuotedString bytes units) :
        JsonValue bytes (.str units)
    | arrayEmpty {ws : List UInt8} (space : Whitespace ws) :
        JsonValue (0x5B :: ws ++ [0x5D]) (.array [])
    | array {left body right : List UInt8} {values : List Value}
        (before : Whitespace left) (items : ArrayElements body values)
        (after : Whitespace right) :
        JsonValue (0x5B :: left ++ body ++ right ++ [0x5D]) (.array values)
    | objectEmpty {ws : List UInt8} (space : Whitespace ws) :
        JsonValue (0x7B :: ws ++ [0x7D]) (.object [])
    | object {left body right : List UInt8} {members : List ((List UInt16) × Value)}
        (before : Whitespace left) (items : ObjectMembers body members)
        (after : Whitespace right) :
        JsonValue (0x7B :: left ++ body ++ right ++ [0x7D]) (.object members)

  inductive ArrayElements : List UInt8 → List Value → Prop where
    | one {bytes : List UInt8} {value : Value} (item : JsonValue bytes value) :
        ArrayElements bytes [value]
    | more {head tail left right : List UInt8} {value : Value} {values : List Value}
        (first : JsonValue head value) (beforeComma : Whitespace left)
        (afterComma : Whitespace right) (following : ArrayElements tail values) :
        ArrayElements (head ++ left ++ [0x2C] ++ right ++ tail) (value :: values)

  inductive Member : List UInt8 → ((List UInt16) × Value) → Prop where
    | member {keyBytes valueBytes left right : List UInt8} {key : List UInt16} {value : Value}
        (name : QuotedString keyBytes key) (beforeColon : Whitespace left)
        (afterColon : Whitespace right) (meaning : JsonValue valueBytes value) :
        Member (keyBytes ++ left ++ [0x3A] ++ right ++ valueBytes) (key, value)

  inductive ObjectMembers : List UInt8 → List ((List UInt16) × Value) → Prop where
    | one {bytes : List UInt8} {entry : (List UInt16) × Value} (item : Member bytes entry) :
        ObjectMembers bytes [entry]
    | more {head tail left right : List UInt8} {entry : (List UInt16) × Value}
        {entries : List ((List UInt16) × Value)}
        (first : Member head entry) (beforeComma : Whitespace left)
        (afterComma : Whitespace right) (following : ObjectMembers tail entries) :
        ObjectMembers (head ++ left ++ [0x2C] ++ right ++ tail) (entry :: entries)
end

/-- Exactly one complete value; only JSON whitespace may surround it. -/
def DocumentBytes (bytes : List UInt8) (value : Value) : Prop :=
  ∃ leading payload trailing : List UInt8,
    Whitespace leading ∧ JsonValue payload value ∧ Whitespace trailing ∧
      bytes = leading ++ payload ++ trailing

def Document (input : ByteArray) (value : Value) : Prop := DocumentBytes input.toList value

/- Independent optional structural budget: root depth zero; each Value and each
object member contributes one node. No implementation fuel or scanner is used. -/
mutual
  inductive ShapeFits : Nat → Nat → Nat → Value → Nat → Prop where
    | null {depth maxDepth maxNumber : Nat} (h : depth ≤ maxDepth) :
        ShapeFits depth maxDepth maxNumber .null 1
    | bool {depth maxDepth maxNumber : Nat} (value : Bool) (h : depth ≤ maxDepth) :
        ShapeFits depth maxDepth maxNumber (.bool value) 1
    | str {depth maxDepth maxNumber : Nat} (units : List UInt16) (h : depth ≤ maxDepth) :
        ShapeFits depth maxDepth maxNumber (.str units) 1
    | number {depth maxDepth maxNumber : Nat} (lexeme : String)
        (h : depth ≤ maxDepth) (tokenSize : lexeme.toUTF8.size ≤ maxNumber) :
        ShapeFits depth maxDepth maxNumber (.number lexeme) 1
    | array {depth maxDepth maxNumber nodes : Nat} {values : List Value}
        (h : depth ≤ maxDepth) (children : ElementsFit (depth + 1) maxDepth maxNumber values nodes) :
        ShapeFits depth maxDepth maxNumber (.array values) (1 + nodes)
    | object {depth maxDepth maxNumber nodes : Nat} {entries : List ((List UInt16) × Value)}
        (h : depth ≤ maxDepth) (children : MembersFit (depth + 1) maxDepth maxNumber entries nodes) :
        ShapeFits depth maxDepth maxNumber (.object entries) (1 + nodes)

  inductive ElementsFit : Nat → Nat → Nat → List Value → Nat → Prop where
    | nil {depth maxDepth maxNumber : Nat} : ElementsFit depth maxDepth maxNumber [] 0
    | cons {depth maxDepth maxNumber headNodes tailNodes : Nat}
        {head : Value} {tail : List Value}
        (first : ShapeFits depth maxDepth maxNumber head headNodes)
        (following : ElementsFit depth maxDepth maxNumber tail tailNodes) :
        ElementsFit depth maxDepth maxNumber (head :: tail) (headNodes + tailNodes)

  inductive MembersFit : Nat → Nat → Nat → List ((List UInt16) × Value) → Nat → Prop where
    | nil {depth maxDepth maxNumber : Nat} : MembersFit depth maxDepth maxNumber [] 0
    | cons {depth maxDepth maxNumber valueNodes tailNodes : Nat}
        {key : List UInt16} {value : Value} {tail : List ((List UInt16) × Value)}
        (first : ShapeFits depth maxDepth maxNumber value valueNodes)
        (following : MembersFit depth maxDepth maxNumber tail tailNodes) :
        MembersFit depth maxDepth maxNumber ((key, value) :: tail) (1 + valueNodes + tailNodes)
end

def FitsLimits (input : ByteArray) (limits : Limits) (value : Value) : Prop :=
  input.size ≤ limits.inputBytes ∧
    ∃ nodes : Nat, ShapeFits 0 limits.depth limits.numberBytes value nodes ∧ nodes ≤ limits.nodes

/-- The UTF-8 constructors cannot denote a surrogate or an out-of-range code point. -/
theorem utf8Scalar_isScalar (bytes : List UInt8) (cp : Nat) (h : Utf8Scalar bytes cp) :
    IsScalar cp := by
  cases h with
  | one a ha => unfold IsScalar; omega
  | two a b ha hb =>
    unfold IsScalar
    unfold IsContinuation at hb
    omega
  | three a b c ha hb hc shortest noSurrogate =>
    unfold IsScalar
    unfold IsContinuation at hb hc
    constructor
    · omega
    · intro surrogate
      have atED : a.toNat = 0xED := by omega
      have upper := noSurrogate atED
      omega
  | four a b c d ha hb hc hd shortest maximum =>
    unfold IsScalar
    unfold IsContinuation at hb hc hd
    constructor
    · by_cases atF4 : a.toNat = 0xF4
      · have upper := maximum atF4
        omega
      · omega
    · have lower :
          0x10000 ≤ (a.toNat - 0xF0) * 262144 + (b.toNat - 0x80) * 4096 +
            (c.toNat - 0x80) * 64 + (d.toNat - 0x80) := by
        by_cases atF0 : a.toNat = 0xF0
        · have first := shortest atF0
          omega
        · omega
      omega

theorem cent_utf8 : Utf8Scalar [0xC2, 0xA2] 0xA2 := by
  exact .two 0xC2 0xA2 (by decide) (by unfold IsContinuation; decide)

theorem euro_utf8 : Utf8Scalar [0xE2, 0x82, 0xAC] 0x20AC := by
  exact .three 0xE2 0x82 0xAC (by decide)
    (by unfold IsContinuation; decide) (by unfold IsContinuation; decide)
    (by decide) (by decide)

theorem musical_symbol_utf8 : Utf8Scalar [0xF0, 0x9D, 0x84, 0x9E] 0x1D11E := by
  exact .four 0xF0 0x9D 0x84 0x9E (by decide)
    (by unfold IsContinuation; decide) (by unfold IsContinuation; decide)
    (by unfold IsContinuation; decide) (by decide) (by decide)

/-- A non-vacuous whole-document witness. -/
theorem null_document : DocumentBytes [0x6E, 0x75, 0x6C, 0x6C] .null := by
  exact ⟨[], _, [], .nil, .null, .nil, rfl⟩

theorem empty_array_document : DocumentBytes [0x5B, 0x5D] (.array []) := by
  exact ⟨[], _, [], .nil, .arrayEmpty .nil, .nil, rfl⟩

theorem string_A : QuotedString [0x22, 0x41, 0x22] [0x41] := by
  apply QuotedString.quoted (body := [0x41])
  exact StringContents.cons
    (.raw (.one 0x41 (by decide)) (by unfold IsScalar; decide)
      (by unfold RawAllowed; decide)) .nil

theorem empty_string : QuotedString [0x22, 0x22] [] := by
  exact QuotedString.quoted (body := []) .nil

theorem escaped_tab : StringPiece [0x5C, 0x74] [0x09] := by
  exact .simple 0x74 0x09 (by unfold SimpleEscape; decide)

/-- Two equal wire names remain two ordered members, rather than a collapsed map. -/
theorem duplicate_members_representable :
    ∃ bytes : List UInt8, JsonValue bytes (.object [([0x41], .null), ([0x41], .bool true)]) := by
  have first : Member [0x22, 0x41, 0x22, 0x3A, 0x6E, 0x75, 0x6C, 0x6C] ([0x41], .null) :=
    .member string_A .nil .nil .null
  have second : Member [0x22, 0x41, 0x22, 0x3A, 0x74, 0x72, 0x75, 0x65]
      ([0x41], .bool true) := .member string_A .nil .nil .boolTrue
  exact ⟨_, .object .nil (.more first .nil .nil (.one second)) .nil⟩

/-- Escaped lone high surrogates are wire units; scalar-profile checks are separate. -/
theorem lone_high_surrogate_string :
    QuotedString [0x22, 0x5C, 0x75, 0x44, 0x38, 0x30, 0x30, 0x22] [0xD800] := by
  apply QuotedString.quoted (body := [0x5C, 0x75, 0x44, 0x38, 0x30, 0x30])
  exact StringContents.cons
    (.unicode 0x44 0x38 0x30 0x30 13 8 0 0
      (by unfold HexDigit; decide) (by unfold HexDigit; decide)
      (by unfold HexDigit; decide) (by unfold HexDigit; decide)) .nil

theorem supplementary_utf16 : scalarToUtf16 0x1D11E = [0xD834, 0xDD1E] := by
  decide +kernel

theorem quote_not_raw : ¬ RawAllowed 0x22 := by unfold RawAllowed; decide
theorem control_not_raw : ¬ RawAllowed 0x1F := by unfold RawAllowed; decide
theorem surrogate_not_scalar : ¬ IsScalar 0xD800 := by unfold IsScalar; decide
theorem above_maximum_not_scalar : ¬ IsScalar 0x110000 := by unfold IsScalar; decide

theorem direct_surrogate_utf8_rejected : ¬ Utf8Scalar [0xED, 0xA0, 0x80] 0xD800 := by
  intro h
  exact surrogate_not_scalar (utf8Scalar_isScalar _ _ h)

theorem above_maximum_utf8_rejected : ¬ Utf8Scalar [0xF4, 0x90, 0x80, 0x80] 0x110000 := by
  intro h
  exact above_maximum_not_scalar (utf8Scalar_isScalar _ _ h)

/-- The two-byte overlong leading-byte range is excluded. -/
theorem overlong_two_rejected (cp : Nat) : ¬ Utf8Scalar [0xC0, 0xAF] cp := by
  intro h
  cases h
  rename_i ha hb
  exact (by decide : ¬ (0xC2 ≤ (0xC0 : UInt8).toNat ∧ (0xC0 : UInt8).toNat ≤ 0xDF)) ha

theorem numberToken_nonempty (bytes : List UInt8) (h : Grammar.NumberToken bytes) : bytes ≠ [] := by
  rcases h with ⟨parts, valid, encoding⟩
  intro empty
  have encodedEmpty : parts.encode = [] := encoding.trans empty
  have lengths := congrArg List.length encodedEmpty
  simp only [Grammar.NumberParts.encode, List.length_append, List.length_nil] at lengths
  have integerEmpty : parts.integer = [] := List.eq_nil_of_length_eq_zero (by omega)
  have invalid := valid.1
  rw [integerEmpty] at invalid
  exact invalid

theorem jsonValue_nonempty (bytes : List UInt8) (value : Value) (h : JsonValue bytes value) :
    bytes ≠ [] := by
  cases h with
  | null => simp
  | boolTrue => simp
  | boolFalse => simp
  | number lexeme grammatical => exact numberToken_nonempty _ grammatical
  | str grammatical => cases grammatical; simp
  | arrayEmpty space => simp
  | array before items after => simp
  | objectEmpty space => simp
  | object before items after => simp

/-- Empty input is not any complete JSON document. -/
theorem empty_not_document (value : Value) : ¬ DocumentBytes [] value := by
  rintro ⟨leading, payload, trailing, _, meaning, _, encoding⟩
  have lengths := congrArg List.length encoding
  simp only [List.length_append, List.length_nil] at lengths
  have payloadEmpty : payload = [] := List.eq_nil_of_length_eq_zero (by omega)
  exact jsonValue_nonempty _ _ meaning payloadEmpty

/-- Empty containers consume one node and fit a root depth limit of zero. -/
theorem empty_array_shape : ShapeFits 0 0 0 (.array []) 1 := by
  exact .array (Nat.le_refl _) .nil

/-- One object entry plus its null value contributes two nodes below the root. -/
theorem one_member_shape : ShapeFits 0 1 0 (.object [([0x61], .null)]) 3 := by
  exact .object (by decide) (.cons (.null (by decide)) .nil)

end VerifiedJson.DocumentSpec
