import Std

/-!
Draft independent wire types for the maintainer bootstrap. This module does not
import an implementation. Contract review and full JSON theorems remain pending.
-/

namespace VerifiedJson

/-- Wire values preserve numeric lexemes, UTF-16 units and ordered object members. -/
inductive Value where
  | null
  | bool (value : Bool)
  | number (lexeme : String)
  | str (units : List UInt16)
  | array (values : List Value)
  | object (members : List ((List UInt16) × Value))
  deriving Repr, BEq, Inhabited

/-- Structural budgets; the document root has depth zero. -/
structure Limits where
  inputBytes : Nat := 1048576
  depth : Nat := 128
  nodes : Nat := 100000
  numberBytes : Nat := 4096
  deriving Repr, BEq

def defaultLimits : Limits := {}

/-- Syntax, encoding, budget and profile failures remain distinct. -/
inductive ErrorKind where
  | syntax
  | utf8
  | limit
  | unsupported
  deriving Repr, BEq, Inhabited

/-- Operation-relative byte offset: parser input or serializer emitted output. -/
structure ParseError where
  kind : ErrorKind
  offset : Nat
  deriving Repr, BEq

end VerifiedJson
