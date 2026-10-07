import VerifiedJson.Number

namespace VerifiedJson

private structure EmitState where
  text : String := ""
  bytes : Nat := 0

private def emitFail (kind : ErrorKind) (offset : Nat) : Except ParseError α :=
  .error { kind, offset }

private def appendChecked (limit : Nat) (state : EmitState) (piece : String) : Except ParseError EmitState :=
  let nextBytes := state.bytes + piece.utf8ByteSize
  if nextBytes > limit then emitFail .limit state.bytes
  else .ok { text := state.text ++ piece, bytes := nextBytes }

private def hexDigit (digit : Nat) : Char :=
  Char.ofNat (if digit < 10 then 48 + digit else 87 + digit)

/-- Always emits ASCII JSON escapes, including for unpaired UTF-16 surrogates. -/
def escapeUnit (unit : UInt16) : String :=
  let n := unit.toNat
  String.ofList ['\\', 'u', hexDigit (n / 4096 % 16), hexDigit (n / 256 % 16),
    hexDigit (n / 16 % 16), hexDigit (n % 16)]

/-- One escaped code unit contributes exactly the six JSON escape characters. -/
theorem escapeUnit_length (unit : UInt16) : (escapeUnit unit).length = 6 := by
  simp [escapeUnit]
  decide +kernel

private def emitUnits (limit : Nat) : List UInt16 → EmitState → Except ParseError EmitState
  | [], state => .ok state
  | unit :: rest, state => do
    let state ← appendChecked limit state (escapeUnit unit)
    emitUnits limit rest state

private def emitString (limit : Nat) (units : List UInt16) (state : EmitState) : Except ParseError EmitState := do
  let state ← appendChecked limit state "\""
  let state ← emitUnits limit units state
  appendChecked limit state "\""

mutual
  private def emitValue (limit : Nat) : Nat → Value → EmitState → Except ParseError EmitState
    | 0, _, state => emitFail .limit state.bytes
    | fuel + 1, value, state =>
      match value with
      | .null => appendChecked limit state "null"
      | .bool flag => appendChecked limit state (if flag then "true" else "false")
      | .number token =>
        if Number.isValidLexeme token then appendChecked limit state token
        else emitFail .syntax state.bytes
      | .str units => emitString limit units state
      | .array values => do
        let state ← appendChecked limit state "["
        let state ← emitArray limit fuel values state true
        appendChecked limit state "]"
      | .object members => do
        let state ← appendChecked limit state "{"
        let state ← emitObject limit fuel members state true
        appendChecked limit state "}"

  private def emitArray (limit : Nat) : Nat → List Value → EmitState → Bool → Except ParseError EmitState
    | 0, _, state, _ => emitFail .limit state.bytes
    | _ + 1, [], state, _ => .ok state
    | fuel + 1, value :: rest, state, first => do
      let state ← if first then .ok state else appendChecked limit state ","
      let state ← emitValue limit fuel value state
      emitArray limit fuel rest state false

  private def emitObject (limit : Nat) :
      Nat → List ((List UInt16) × Value) → EmitState → Bool → Except ParseError EmitState
    | 0, _, state, _ => emitFail .limit state.bytes
    | _ + 1, [], state, _ => .ok state
    | fuel + 1, (key, value) :: rest, state, first => do
      let state ← if first then .ok state else appendChecked limit state ","
      let state ← emitString limit key state
      let state ← appendChecked limit state ":"
      let state ← emitValue limit fuel value state
      emitObject limit fuel rest state false
end

/-- Serialize a candidate wire AST as ASCII JSON, preserving member order, duplicate names,
number lexemes and UTF-16 units. Invalid handcrafted number tokens are rejected.
Error offsets for this AST-input API count already emitted output bytes. -/
def serialize (value : Value) (outputLimit : Nat := 8388608) : Except ParseError String := do
  let state ← emitValue outputLimit (outputLimit + 2) value {}
  .ok state.text

end VerifiedJson
