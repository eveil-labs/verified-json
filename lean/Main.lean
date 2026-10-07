import VerifiedJson

open VerifiedJson

private def code : ErrorKind → String
  | .syntax => "syntax"
  | .utf8 => "utf8"
  | .limit => "limit"
  | .unsupported => "unsupported"

private def readRequest (stream : IO.FS.Stream) (fuel : Nat) (cap : Nat)
    (acc : ByteArray := ByteArray.empty) : IO (Except String ByteArray) := do
  match fuel with
  | 0 => return .error "request bound exhausted"
  | fuel + 1 =>
    let next ← stream.read (min 4096 (cap + 1 - acc.size)).toUSize
    if next.isEmpty then return .ok acc
    if acc.size + next.size > cap then return .error "request too large"
    readRequest stream fuel cap (acc ++ next)

private def body (bytes : ByteArray) : Except String String := do
  let some text := String.fromUTF8? bytes | .error "non-ASCII request"
  let chars := match text.toList.reverse with
    | '\n' :: rest => rest.reverse
    | other => other.reverse
  return String.ofList chars

private def response (input : ByteArray) (serializeMode : Bool) : String :=
  match parseDocument input with
  | .error e => s!"VJ1\terr\t{code e.kind}\t{e.offset}"
  | .ok value =>
    if serializeMode then
      match serialize value with
      | .ok text => s!"VJ1\tjson\t{Transport.toHex text.toUTF8}"
      | .error e => s!"VJ1\terr\t{code e.kind}\t{e.offset}"
    else
      match Transport.encode value with
      | .ok bytes => s!"VJ1\tok\t{Transport.toHex bytes}"
      | .error e => s!"VJ1\terr\t{code e.kind}\t{e.offset}"

/-- One bounded, synthetic-data oracle request per process; no reporting side effects. -/
def main (args : List String) : IO UInt32 := do
  if args != [] && args != ["--serialize"] then
    (← IO.getStderr).putStrLn "usage: verified-json-oracle [--serialize]"
    return 2
  let cap := 2 * defaultLimits.inputBytes + 3
  let request ← readRequest (← IO.getStdin) (cap + 2) cap
  let decoded := do
    let bytes ← request
    let text ← body bytes
    Transport.fromHex text
  let stdout ← IO.getStdout
  match decoded with
  | .error _ => stdout.putStrLn "VJ1\terr\ttransport\t0"; return 2
  | .ok input => stdout.putStrLn (response input (args == ["--serialize"])); return 0
