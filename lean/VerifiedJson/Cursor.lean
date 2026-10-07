import Std

namespace VerifiedJson

/-- An immutable byte cursor with an explicit endpoint bound. -/
structure Cursor where
  input : ByteArray
  pos : Nat
  bound : pos ≤ input.size

namespace Cursor

def start (input : ByteArray) : Cursor := ⟨input, 0, Nat.zero_le _⟩

def remaining (cursor : Cursor) : Nat := cursor.input.size - cursor.pos

def peek (cursor : Cursor) : Option UInt8 :=
  if h : cursor.pos < cursor.input.size then
    some (cursor.input.get cursor.pos h)
  else none

def advance (cursor : Cursor) : Option Cursor :=
  if h : cursor.pos < cursor.input.size then
    some ⟨cursor.input, cursor.pos + 1, by omega⟩
  else none

theorem start_pos (input : ByteArray) : (start input).pos = 0 := rfl

theorem peek_none_iff (cursor : Cursor) : peek cursor = none ↔ cursor.pos = cursor.input.size := by
  unfold peek
  split
  · simp only [Option.some_ne_none, false_iff]
    omega
  · simp only [true_iff]
    have := cursor.bound
    omega

theorem advance_none_iff (cursor : Cursor) :
    advance cursor = none ↔ cursor.pos = cursor.input.size := by
  unfold advance
  split
  · simp only [Option.some_ne_none, false_iff]
    omega
  · simp only [true_iff]
    have := cursor.bound
    omega

theorem advance_progress (cursor next : Cursor) (h : advance cursor = some next) :
    next.input = cursor.input ∧ next.pos = cursor.pos + 1 ∧ next.pos ≤ cursor.input.size := by
  unfold advance at h
  split at h
  · cases h
    simp only [true_and]
    omega
  · contradiction

end Cursor
end VerifiedJson
