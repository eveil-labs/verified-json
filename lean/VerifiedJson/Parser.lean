import VerifiedJson.String
import VerifiedJson.Number

namespace VerifiedJson

private structure ParserContext where
  input : ByteArray
  limits : Limits

private structure ParserState where
  pos : Nat
  nodes : Nat

private def parserFail (kind : ErrorKind) (offset : Nat) : Except ParseError α :=
  .error { kind, offset }

private def parserByte (input : ByteArray) (pos : Nat) : Option Nat :=
  (input[pos]?).map UInt8.toNat

private def jsonWhitespace (b : Nat) : Bool :=
  b == 32 || b == 9 || b == 10 || b == 13

private def skipWhitespaceLoop (input : ByteArray) : Nat → Nat → Nat
  | 0, pos => pos
  | fuel + 1, pos =>
    match parserByte input pos with
    | some b => if jsonWhitespace b then skipWhitespaceLoop input fuel (pos + 1) else pos
    | none => pos

private def skipWhitespace (ctx : ParserContext) (state : ParserState) : ParserState :=
  { state with pos := skipWhitespaceLoop ctx.input (ctx.input.size + 1) state.pos }

private def countNode (ctx : ParserContext) (state : ParserState) : Except ParseError ParserState :=
  if state.nodes ≥ ctx.limits.nodes then parserFail .limit state.pos
  else .ok { state with nodes := state.nodes + 1 }

private def matchLiteral (input : ByteArray) : Nat → List Nat → Bool
  | _, [] => true
  | pos, b :: rest => parserByte input pos == some b && matchLiteral input (pos + 1) rest

mutual
  private def parseValue (ctx : ParserContext) :
      Nat → ParserState → Nat → Except ParseError (Value × ParserState)
    | 0, state, _ => parserFail .limit state.pos
    | fuel + 1, initial, depth => do
      let state := skipWhitespace ctx initial
      if depth > ctx.limits.depth then parserFail .limit state.pos
      else
        let state ← countNode ctx state
        let some b := parserByte ctx.input state.pos | parserFail .syntax state.pos
        if b == 34 then
          let (units, next) ← StringParser.parse ctx.input state.pos
          .ok (.str units, { state with pos := next })
        else if b == 91 then
          parseArray ctx fuel { state with pos := state.pos + 1 } depth [] true
        else if b == 123 then
          parseObject ctx fuel { state with pos := state.pos + 1 } depth [] true
        else if b == 110 then
          if matchLiteral ctx.input state.pos [110, 117, 108, 108] then
            .ok (.null, { state with pos := state.pos + 4 })
          else parserFail .syntax state.pos
        else if b == 116 then
          if matchLiteral ctx.input state.pos [116, 114, 117, 101] then
            .ok (.bool true, { state with pos := state.pos + 4 })
          else parserFail .syntax state.pos
        else if b == 102 then
          if matchLiteral ctx.input state.pos [102, 97, 108, 115, 101] then
            .ok (.bool false, { state with pos := state.pos + 5 })
          else parserFail .syntax state.pos
        else if b == 45 || (48 ≤ b && b ≤ 57) then
          let number ← Number.parse ctx.input state.pos ctx.limits.numberBytes
          .ok (.number number.lexeme, { state with pos := number.endPos })
        else parserFail .syntax state.pos

  private def parseArray (ctx : ParserContext) :
      Nat → ParserState → Nat → List Value → Bool → Except ParseError (Value × ParserState)
    | 0, state, _, _, _ => parserFail .limit state.pos
    | fuel + 1, initial, depth, reversed, allowEmpty => do
      let state := skipWhitespace ctx initial
      if parserByte ctx.input state.pos == some 93 then
        if allowEmpty then .ok (.array reversed.reverse, { state with pos := state.pos + 1 })
        else parserFail .syntax state.pos
      else
        let (value, after) ← parseValue ctx fuel state (depth + 1)
        let after := skipWhitespace ctx after
        let some delimiter := parserByte ctx.input after.pos | parserFail .syntax after.pos
        if delimiter == 93 then .ok (.array (value :: reversed).reverse, { after with pos := after.pos + 1 })
        else if delimiter == 44 then
          parseArray ctx fuel { after with pos := after.pos + 1 } depth (value :: reversed) false
        else parserFail .syntax after.pos

  private def parseObject (ctx : ParserContext) :
      Nat → ParserState → Nat → List ((List UInt16) × Value) → Bool → Except ParseError (Value × ParserState)
    | 0, state, _, _, _ => parserFail .limit state.pos
    | fuel + 1, initial, depth, reversed, allowEmpty => do
      let state := skipWhitespace ctx initial
      if parserByte ctx.input state.pos == some 125 then
        if allowEmpty then .ok (.object reversed.reverse, { state with pos := state.pos + 1 })
        else parserFail .syntax state.pos
      else
        let state ← countNode ctx state
        let (key, next) ← StringParser.parse ctx.input state.pos
        let afterKey := skipWhitespace ctx { state with pos := next }
        if parserByte ctx.input afterKey.pos != some 58 then parserFail .syntax afterKey.pos
        else
          let (value, after) ← parseValue ctx fuel { afterKey with pos := afterKey.pos + 1 } (depth + 1)
          let after := skipWhitespace ctx after
          let some delimiter := parserByte ctx.input after.pos | parserFail .syntax after.pos
          if delimiter == 125 then
            .ok (.object ((key, value) :: reversed).reverse, { after with pos := after.pos + 1 })
          else if delimiter == 44 then
            parseObject ctx fuel { after with pos := after.pos + 1 } depth ((key, value) :: reversed) false
          else parserFail .syntax after.pos
end

/-- Candidate complete-document parser. Operational fuel exhaustion is a limit outcome,
not evidence that an input is syntactically invalid. Root depth is zero. -/
def parseDocument (input : ByteArray) (limits : Limits := {}) : Except ParseError Value := do
  if input.size > limits.inputBytes then parserFail .limit 0
  else
    let ctx := { input, limits : ParserContext }
    let (value, after) ← parseValue ctx (4 * input.size + 16) { pos := 0, nodes := 0 } 0
    let after := skipWhitespace ctx after
    if after.pos == input.size then .ok value else parserFail .syntax after.pos

end VerifiedJson
