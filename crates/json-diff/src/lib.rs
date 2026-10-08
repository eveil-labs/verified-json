//! Draft comparison infrastructure. No all-input correctness or sandbox claim.

use json_wire::{contains_non_scalar, decode, encode, hex_decode, Limits, WireValue};
use serde::de::{DeserializeSeed, Error as _, MapAccess, SeqAccess, Visitor};
use serde::{Deserialize, Deserializer};
use serde_json::value::RawValue;
use std::fmt;
use std::io::{Read, Write};
use std::path::Path;
use std::process::{Child, Command, Stdio};
use std::time::{Duration, Instant};

pub const INPUT_LIMIT: usize = 1024 * 1024;
pub const STDERR_LIMIT: usize = 64 * 1024;
pub const CANDIDATE_DEPTH_LIMIT: usize = 64;
pub const PROFILE: &str =
    "serde_json-1.0.151/raw_value+std/custom-sequence/scalar-strings/exact-number-tokens";

#[derive(Debug, PartialEq, Eq)]
pub enum CandidateOutcome {
    Accepted(WireValue),
    Rejected {
        category: String,
        line: usize,
        column: usize,
    },
    Limit {
        resource: &'static str,
    },
}

struct CandidateBudget {
    limits: Limits,
    nodes: usize,
    units: usize,
    failed: Option<&'static str>,
}
impl CandidateBudget {
    fn refuse<E: serde::de::Error>(&mut self, kind: &'static str) -> E {
        self.failed = Some(kind);
        E::custom("candidate operational budget exceeded")
    }
    fn node<E: serde::de::Error>(&mut self, depth: usize) -> Result<(), E> {
        if depth > self.limits.max_depth {
            return Err(self.refuse("depth"));
        }
        self.nodes = self
            .nodes
            .checked_add(1)
            .filter(|&n| n <= self.limits.max_nodes)
            .ok_or_else(|| self.refuse("nodes"))?;
        Ok(())
    }
    fn member<E: serde::de::Error>(&mut self) -> Result<(), E> {
        self.nodes = self
            .nodes
            .checked_add(1)
            .filter(|&n| n <= self.limits.max_nodes)
            .ok_or_else(|| self.refuse("nodes"))?;
        Ok(())
    }
    fn units<E: serde::de::Error>(&mut self, text: &str) -> Result<Vec<u16>, E> {
        let count = text.encode_utf16().count();
        self.units = self
            .units
            .checked_add(count)
            .filter(|&n| n <= self.limits.max_units)
            .ok_or_else(|| self.refuse("units"))?;
        Ok(text.encode_utf16().collect())
    }
}

struct Seed<'a> {
    budget: &'a mut CandidateBudget,
    depth: usize,
}
impl<'de> DeserializeSeed<'de> for Seed<'_> {
    type Value = WireValue;
    fn deserialize<D: Deserializer<'de>>(self, deserializer: D) -> Result<Self::Value, D::Error> {
        // RawValue avoids any fixed-precision number conversion before our visitor.
        let raw = Box::<RawValue>::deserialize(deserializer)?;
        parse_raw(raw.get(), self.budget, self.depth).map_err(D::Error::custom)
    }
}

struct SequenceVisitor<'a> {
    budget: &'a mut CandidateBudget,
    depth: usize,
}
impl<'de> Visitor<'de> for SequenceVisitor<'_> {
    type Value = WireValue;
    fn expecting(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("a JSON array")
    }
    fn visit_seq<A: SeqAccess<'de>>(self, mut seq: A) -> Result<Self::Value, A::Error> {
        let mut values = Vec::new();
        while let Some(value) = seq.next_element_seed(Seed {
            budget: &mut *self.budget,
            depth: self.depth + 1,
        })? {
            values.push(value);
        }
        Ok(WireValue::Array(values))
    }
}

struct ObjectVisitor<'a> {
    budget: &'a mut CandidateBudget,
    depth: usize,
}
impl<'de> Visitor<'de> for ObjectVisitor<'_> {
    type Value = WireValue;
    fn expecting(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("a JSON object")
    }
    fn visit_map<A: MapAccess<'de>>(self, mut map: A) -> Result<Self::Value, A::Error> {
        let mut members = Vec::new();
        while let Some(key) = map.next_key::<String>()? {
            self.budget.member::<A::Error>()?;
            let units = self.budget.units::<A::Error>(&key)?;
            let value = map.next_value_seed(Seed {
                budget: &mut *self.budget,
                depth: self.depth + 1,
            })?;
            members.push((units, value));
        }
        Ok(WireValue::Object(members))
    }
}

fn parse_raw(
    raw: &str,
    budget: &mut CandidateBudget,
    depth: usize,
) -> Result<WireValue, serde_json::Error> {
    budget.node::<serde_json::Error>(depth)?;
    match raw.as_bytes().first() {
        Some(b'n') if raw == "null" => Ok(WireValue::Null),
        Some(b'f') if raw == "false" => Ok(WireValue::Bool(false)),
        Some(b't') if raw == "true" => Ok(WireValue::Bool(true)),
        Some(b'"') => {
            let text = serde_json::from_str::<String>(raw)?;
            Ok(WireValue::String(budget.units::<serde_json::Error>(&text)?))
        }
        Some(b'[') => {
            let mut deserializer = serde_json::Deserializer::from_str(raw);
            let result = deserializer.deserialize_seq(SequenceVisitor { budget, depth })?;
            deserializer.end()?;
            Ok(result)
        }
        Some(b'{') => {
            let mut deserializer = serde_json::Deserializer::from_str(raw);
            let result = deserializer.deserialize_map(ObjectVisitor { budget, depth })?;
            deserializer.end()?;
            Ok(result)
        }
        Some(b'-' | b'0'..=b'9') => {
            if raw.len() > budget.limits.max_number_bytes {
                return Err(budget.refuse("number"));
            }
            if !json_wire::valid_number_token(raw.as_bytes()) {
                return Err(serde_json::Error::custom(
                    "unexpected invalid RawValue number",
                ));
            }
            Ok(WireValue::Number(raw.as_bytes().to_vec()))
        }
        _ => Err(serde_json::Error::custom("unexpected RawValue constructor")),
    }
}

/// Resource preflight before serde can traverse a deeply nested RawValue.
/// It is deliberately an operational cap, not a JSON validity judgment.
fn nesting_exceeds(bytes: &[u8], max_depth: usize) -> bool {
    let mut depth = 0usize;
    let mut in_string = false;
    let mut escaped = false;
    for &byte in bytes {
        if in_string {
            if escaped {
                escaped = false;
            } else if byte == b'\\' {
                escaped = true;
            } else if byte == b'"' {
                in_string = false;
            }
        } else {
            match byte {
                b'"' => in_string = true,
                b'[' | b'{' => {
                    depth += 1;
                    if depth > max_depth + 1 {
                        return true;
                    }
                }
                b']' | b'}' => depth = depth.saturating_sub(1),
                _ => {}
            }
        }
    }
    false
}

pub fn parse_candidate(bytes: &[u8], mut limits: Limits) -> CandidateOutcome {
    if bytes.len() > INPUT_LIMIT {
        return CandidateOutcome::Limit { resource: "input" };
    }
    limits.max_depth = limits.max_depth.min(CANDIDATE_DEPTH_LIMIT);
    if nesting_exceeds(bytes, limits.max_depth) {
        return CandidateOutcome::Limit { resource: "depth" };
    }
    let mut budget = CandidateBudget {
        limits,
        nodes: 0,
        units: 0,
        failed: None,
    };
    let mut deserializer = serde_json::Deserializer::from_slice(bytes);
    let result = Seed {
        budget: &mut budget,
        depth: 0,
    }
    .deserialize(&mut deserializer)
    .and_then(|value| {
        deserializer.end()?;
        Ok(value)
    });
    match result {
        Ok(value) => match encode(&value, limits) {
            Ok(_) => CandidateOutcome::Accepted(value),
            Err(error) if error.kind.is_limit() => CandidateOutcome::Limit {
                resource: "wire_output",
            },
            Err(_) => CandidateOutcome::Rejected {
                category: "adapter_codec".into(),
                line: 0,
                column: 0,
            },
        },
        Err(error) => {
            if let Some(resource) = budget.failed {
                CandidateOutcome::Limit { resource }
            } else {
                CandidateOutcome::Rejected {
                    category: format!("{:?}", error.classify()),
                    line: error.line(),
                    column: error.column(),
                }
            }
        }
    }
}

#[derive(Debug, PartialEq, Eq)]
pub enum OracleOutcome {
    Accepted(WireValue),
    Error { code: String, offset: usize },
}

#[derive(Debug, PartialEq, Eq)]
pub enum OracleFailure {
    Io(String),
    Timeout,
    OutputLimit(&'static str),
    Exit(Option<i32>),
    Protocol(&'static str),
    WireLimit(String),
    Cleanup(String),
    WithCleanup {
        primary: Box<OracleFailure>,
        cleanup: Box<OracleFailure>,
    },
}

impl OracleFailure {
    /// Retain the observed protocol/limit/IO failure if teardown also failed.
    pub fn primary(&self) -> &Self {
        let mut failure = self;
        while let Self::WithCleanup { primary, .. } = failure {
            failure = primary;
        }
        failure
    }
}

pub fn parse_response(
    bytes: &[u8],
    input_len: usize,
    limits: Limits,
) -> Result<OracleOutcome, OracleFailure> {
    let line = bytes.strip_suffix(b"\n").unwrap_or(bytes);
    if line.contains(&b'\n') || line.contains(&b'\r') {
        return Err(OracleFailure::Protocol("response must be one ASCII line"));
    }
    let fields: Vec<&[u8]> = line.split(|&b| b == b'\t').collect();
    match fields.as_slice() {
        [b"VJ1", b"ok", hex] => {
            let wire = hex_decode(hex, limits.max_bytes).map_err(|error| match error {
                json_wire::HexError::Limit => OracleFailure::WireLimit("hex frame".into()),
                _ => OracleFailure::Protocol("invalid AST hex"),
            })?;
            let value = decode(&wire, limits).map_err(|error| {
                if error.kind.is_limit() {
                    OracleFailure::WireLimit(error.to_string())
                } else {
                    OracleFailure::Protocol("invalid neutral AST")
                }
            })?;
            Ok(OracleOutcome::Accepted(value))
        }
        [b"VJ1", b"err", code, offset] => {
            let code =
                std::str::from_utf8(code).map_err(|_| OracleFailure::Protocol("non-ASCII code"))?;
            if !matches!(
                code,
                "syntax" | "utf8" | "limit" | "unsupported" | "transport"
            ) {
                return Err(OracleFailure::Protocol("unknown error code"));
            }
            if code.len() > 64
                || !code
                    .bytes()
                    .all(|b| b.is_ascii_lowercase() || b.is_ascii_digit() || b == b'_')
            {
                return Err(OracleFailure::Protocol("invalid error code"));
            }
            if offset.is_empty() || offset.len() > 20 || !offset.iter().all(u8::is_ascii_digit) {
                return Err(OracleFailure::Protocol("invalid error offset"));
            }
            let offset = std::str::from_utf8(offset)
                .unwrap()
                .parse::<usize>()
                .map_err(|_| OracleFailure::Protocol("error offset overflow"))?;
            if offset > input_len {
                return Err(OracleFailure::Protocol("error offset outside input"));
            }
            Ok(OracleOutcome::Error {
                code: code.into(),
                offset,
            })
        }
        _ => Err(OracleFailure::Protocol("invalid response fields/version")),
    }
}

#[derive(Debug)]
pub struct OracleRun {
    pub outcome: OracleOutcome,
    pub stderr_bytes: usize,
}

#[cfg(unix)]
fn nonblocking(fd: &impl std::os::fd::AsFd) -> Result<(), OracleFailure> {
    let flags =
        rustix::fs::fcntl_getfl(fd).map_err(|error| OracleFailure::Io(error.to_string()))?;
    rustix::fs::fcntl_setfl(fd, flags | rustix::fs::OFlags::NONBLOCK)
        .map_err(|error| OracleFailure::Io(error.to_string()))
}

#[cfg(unix)]
fn drain_pipe(
    stream: &mut impl Read,
    output: &mut Vec<u8>,
    eof: &mut bool,
    cap: usize,
    name: &'static str,
) -> Result<(), OracleFailure> {
    if *eof {
        return Ok(());
    }
    let mut buffer = [0u8; 8192];
    // Bounded progress per iteration keeps an output flood from starving the deadline.
    for _ in 0..8 {
        match stream.read(&mut buffer) {
            Ok(0) => {
                *eof = true;
                return Ok(());
            }
            Ok(count) => {
                if count > cap.saturating_sub(output.len()) {
                    return Err(OracleFailure::OutputLimit(name));
                }
                output
                    .try_reserve(count)
                    .map_err(|_| OracleFailure::Io("output allocation failed".into()))?;
                output.extend_from_slice(&buffer[..count]);
            }
            Err(error) if error.kind() == std::io::ErrorKind::WouldBlock => return Ok(()),
            Err(error) if error.kind() == std::io::ErrorKind::Interrupted => continue,
            Err(error) => return Err(OracleFailure::Io(error.to_string())),
        }
    }
    Ok(())
}

#[cfg(unix)]
fn child_pid(child: &Child) -> std::io::Result<rustix::process::Pid> {
    let raw_pid = child.id();
    if raw_pid <= 1 || raw_pid > i32::MAX as u32 {
        return Err(std::io::Error::other("invalid child process identity"));
    }
    rustix::process::Pid::from_raw(raw_pid as i32)
        .ok_or_else(|| std::io::Error::other("invalid child process identity"))
}

#[cfg(unix)]
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
struct ChildExit {
    code: Option<i32>,
}

// rustix 1.1.5 does not provide the needed waitid/status API on these targets.
// Refuse before spawning instead of falling back to a reaping completion poll.
#[cfg(unix)]
const HAS_WAITID: bool = !cfg!(any(
    target_os = "cygwin",
    target_os = "espidf",
    target_os = "horizon",
    target_os = "openbsd",
    target_os = "redox",
    target_os = "vita",
    target_os = "wasi",
    target_os = "emscripten",
    target_os = "fuchsia",
    target_os = "netbsd",
));

#[cfg(unix)]
fn observe_child_exit(child: &Child) -> std::io::Result<Option<ChildExit>> {
    #[cfg(not(any(
        target_os = "cygwin",
        target_os = "espidf",
        target_os = "horizon",
        target_os = "openbsd",
        target_os = "redox",
        target_os = "vita",
        target_os = "wasi",
        target_os = "emscripten",
        target_os = "fuchsia",
        target_os = "netbsd",
    )))]
    {
        use rustix::process::{waitid, WaitId, WaitIdOptions};
        // Keep the leader waitable, including after exit, until group signaling
        // has finished. A reaping poll here would make its PID reusable.
        let status = waitid(
            WaitId::Pid(child_pid(child)?),
            WaitIdOptions::EXITED | WaitIdOptions::NOHANG | WaitIdOptions::NOWAIT,
        )?;
        status
            .map(|status| {
                if status.exited() || status.killed() || status.dumped() {
                    Ok(ChildExit {
                        code: status.exit_status(),
                    })
                } else {
                    Err(std::io::Error::other("unexpected child waitid status"))
                }
            })
            .transpose()
    }
    #[cfg(any(
        target_os = "cygwin",
        target_os = "espidf",
        target_os = "horizon",
        target_os = "openbsd",
        target_os = "redox",
        target_os = "vita",
        target_os = "wasi",
        target_os = "emscripten",
        target_os = "fuchsia",
        target_os = "netbsd",
    ))]
    {
        let _ = child;
        Err(std::io::Error::new(
            std::io::ErrorKind::Unsupported,
            "non-reaping child observation unavailable on this platform",
        ))
    }
}

// The seam keeps cleanup ordering independently testable without PID churn or
// signals to unrelated processes. Only reap() may consume the child status.
#[cfg(unix)]
trait ProcessControl {
    fn observe(&self) -> std::io::Result<Option<ChildExit>>;
    fn signal_group(&mut self) -> std::io::Result<()>;
    fn kill_direct(&mut self) -> std::io::Result<()>;
    fn reap(&mut self) -> std::io::Result<bool>;
}

#[cfg(unix)]
impl ProcessControl for Child {
    fn observe(&self) -> std::io::Result<Option<ChildExit>> {
        observe_child_exit(self)
    }
    fn signal_group(&mut self) -> std::io::Result<()> {
        rustix::process::kill_process_group(child_pid(self)?, rustix::process::Signal::KILL)
            .map_err(Into::into)
    }
    fn kill_direct(&mut self) -> std::io::Result<()> {
        self.kill()
    }
    fn reap(&mut self) -> std::io::Result<bool> {
        self.try_wait().map(|status| status.is_some())
    }
}

#[cfg(unix)]
#[derive(Clone, Copy, PartialEq, Eq)]
enum CleanupMode {
    CompletedExchange,
    Stop,
}

#[cfg(unix)]
fn cleanup_process(
    process: &mut impl ProcessControl,
    mode: CleanupMode,
    cleanup_budget: Duration,
) -> Result<(), OracleFailure> {
    let deadline = Instant::now() + cleanup_budget;
    // An embedding caller must not independently reap this child or enable
    // SIGCHLD auto-reaping. Refuse to signal if lost waitable ownership is observed.
    let observed = loop {
        match process.observe() {
            Ok(observed) => break observed,
            Err(error) if error.kind() == std::io::ErrorKind::Interrupted => {
                if Instant::now() >= deadline {
                    return Err(OracleFailure::Cleanup(
                        "child ownership observation interrupted until cleanup deadline; no signals sent".into(),
                    ));
                }
            }
            Err(error) => {
                return Err(OracleFailure::Cleanup(format!(
                    "waitable child ownership not established: {error}; no signals sent"
                )))
            }
        }
    };
    let group_issue = if mode == CleanupMode::CompletedExchange {
        if observed != Some(ChildExit { code: Some(0) }) {
            return Err(OracleFailure::Cleanup(
                "completed exchange has no waitable successful child exit; no signals sent".into(),
            ));
        }
        // A valid exchange has already observed exit 0 and EOF on both pipes.
        // Only reap the direct child. This does not prove there are no silent
        // descendants, and avoids Darwin's ambiguous zombie-only killpg EPERM.
        None
    } else {
        let issue = match process.signal_group() {
            Ok(()) => None,
            Err(error) if error.raw_os_error() == Some(rustix::io::Errno::SRCH.raw_os_error()) => {
                None
            }
            Err(error) => Some(format!(
                "process-group termination not established: {error:?}"
            )),
        };
        // Every signal precedes the first reap. Never signal a numeric identity
        // after reap() has made the leader PID eligible for reuse.
        let _ = process.kill_direct();
        issue
    };
    loop {
        match process.reap() {
            Ok(true) => {
                return group_issue.map_or(Ok(()), |detail| {
                    Err(OracleFailure::Cleanup(format!(
                        "{detail}; direct child reaped after bounded fallback"
                    )))
                })
            }
            Ok(false) => {}
            Err(error) if error.kind() == std::io::ErrorKind::Interrupted => {}
            Err(error) => {
                return Err(OracleFailure::Cleanup(format!(
                    "direct-child reaping not established: {error}; group issue={group_issue:?}"
                )))
            }
        }
        if Instant::now() >= deadline {
            return Err(OracleFailure::Cleanup(
                format!("direct-child termination not observed before cleanup deadline; group issue={group_issue:?}"),
            ));
        }
        std::thread::sleep(Duration::from_millis(2));
    }
}

#[cfg(unix)]
fn finish_run(
    result: Result<OracleRun, OracleFailure>,
    cleanup: Result<(), OracleFailure>,
) -> Result<OracleRun, OracleFailure> {
    match (result, cleanup) {
        (Ok(run), Ok(())) => Ok(run),
        (Err(primary), Ok(())) => Err(primary),
        (Ok(_), Err(cleanup)) => Err(cleanup),
        (Err(primary), Err(cleanup)) => Err(OracleFailure::WithCleanup {
            primary: Box::new(primary),
            cleanup: Box::new(cleanup),
        }),
    }
}

#[cfg(not(unix))]
pub fn run_oracle(
    _path: &Path,
    _input: &[u8],
    _timeout: Duration,
    _limits: Limits,
) -> Result<OracleRun, OracleFailure> {
    Err(OracleFailure::Io(
        "nonblocking oracle transport is implemented only on Unix".into(),
    ))
}

#[cfg(unix)]
pub fn run_oracle(
    path: &Path,
    input: &[u8],
    timeout: Duration,
    limits: Limits,
) -> Result<OracleRun, OracleFailure> {
    if !HAS_WAITID {
        return Err(OracleFailure::Io(
            "non-reaping child observation unavailable on this platform".into(),
        ));
    }
    if input.len() > INPUT_LIMIT {
        return Err(OracleFailure::WireLimit("input".into()));
    }
    if timeout.is_zero() || timeout > Duration::from_secs(60) {
        return Err(OracleFailure::Io("invalid timeout".into()));
    }
    let canonical = path
        .canonicalize()
        .map_err(|error| OracleFailure::Io(error.to_string()))?;
    if !canonical.is_file() {
        return Err(OracleFailure::Io("oracle is not a regular file".into()));
    }
    let output_limit = limits
        .max_bytes
        .checked_mul(2)
        .and_then(|n| n.checked_add(96))
        .ok_or(OracleFailure::Io("output limit overflow".into()))?;
    let mut command = Command::new(canonical);
    command
        .env_clear()
        .env("PATH", "/usr/bin:/bin:/usr/sbin:/sbin")
        .env("LANG", "C")
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());
    {
        use std::os::unix::process::CommandExt;
        command.process_group(0);
    }
    let mut child = command
        .spawn()
        .map_err(|error| OracleFailure::Io(error.to_string()))?;
    let mut status = None;
    let result = (|| {
        let mut stdin = Some(child.stdin.take().unwrap());
        let mut stdout = child.stdout.take().unwrap();
        let mut stderr = child.stderr.take().unwrap();
        nonblocking(stdin.as_ref().unwrap())?;
        nonblocking(&stdout)?;
        nonblocking(&stderr)?;
        let mut request = json_wire::hex_encode(input).into_bytes();
        request.push(b'\n');
        let mut written = 0;
        let mut output = Vec::new();
        let mut diagnostics = Vec::new();
        let mut output_eof = false;
        let mut diagnostics_eof = false;
        let started = Instant::now();
        loop {
            if let Some(writer) = stdin.as_mut() {
                let end = request.len().min(written + 8192);
                match writer.write(&request[written..end]) {
                    Ok(0) => {
                        return Err(OracleFailure::Io(
                            "oracle input pipe closed before request completion".into(),
                        ))
                    }
                    Ok(count) => written += count,
                    Err(error)
                        if matches!(
                            error.kind(),
                            std::io::ErrorKind::WouldBlock | std::io::ErrorKind::Interrupted
                        ) => {}
                    Err(error) => return Err(OracleFailure::Io(error.to_string())),
                }
                if written == request.len() {
                    stdin = None;
                }
            }
            drain_pipe(
                &mut stdout,
                &mut output,
                &mut output_eof,
                output_limit,
                "stdout",
            )?;
            drain_pipe(
                &mut stderr,
                &mut diagnostics,
                &mut diagnostics_eof,
                STDERR_LIMIT,
                "stderr",
            )?;
            if status.is_none() {
                match observe_child_exit(&child) {
                    Ok(observed) => status = observed,
                    Err(error) if error.kind() == std::io::ErrorKind::Interrupted => {}
                    Err(error) => return Err(OracleFailure::Io(error.to_string())),
                }
            }
            if let Some(exit) = status.as_ref() {
                if output_eof && diagnostics_eof && stdin.is_none() {
                    if exit.code != Some(0) {
                        return Err(OracleFailure::Exit(exit.code));
                    }
                    let outcome = parse_response(&output, input.len(), limits)?;
                    return Ok(OracleRun {
                        outcome,
                        stderr_bytes: diagnostics.len(),
                    });
                }
            }
            if started.elapsed() >= timeout {
                return Err(OracleFailure::Timeout);
            }
            std::thread::sleep(Duration::from_millis(2));
        }
    })();
    // All caller-owned pipes have been dropped before cleanup: no detached I/O
    // threads or blocked joins remain, even if an escaped descendant holds pipes.
    let mode = if result.is_ok() {
        CleanupMode::CompletedExchange
    } else {
        CleanupMode::Stop
    };
    finish_run(
        result,
        cleanup_process(&mut child, mode, Duration::from_millis(250)),
    )
}

/// Classifies observations, never an all-input proof or an upstream bug verdict.
pub fn classify(oracle: &OracleOutcome, candidate: &CandidateOutcome) -> &'static str {
    match (oracle, candidate) {
        (OracleOutcome::Error { code, .. }, _) if code == "transport" => {
            "oracle_infrastructure_failure"
        }
        (OracleOutcome::Error { code, .. }, _) if code == "unsupported" => "oracle_unsupported",
        (OracleOutcome::Error { code, .. }, _) if code == "limit" => "oracle_limit",
        (_, CandidateOutcome::Limit { .. }) => "candidate_limit",
        (OracleOutcome::Accepted(expected), CandidateOutcome::Accepted(actual))
            if expected == actual =>
        {
            "agreement"
        }
        (OracleOutcome::Accepted(_), CandidateOutcome::Accepted(_)) => "semantic_discrepancy",
        (OracleOutcome::Accepted(value), CandidateOutcome::Rejected { .. })
            if contains_non_scalar(value) =>
        {
            "scalar_profile_difference"
        }
        (OracleOutcome::Accepted(_), CandidateOutcome::Rejected { .. }) => {
            "candidate_rejected_oracle_accepted"
        }
        (OracleOutcome::Error { .. }, CandidateOutcome::Accepted(_)) => {
            "oracle_rejected_candidate_accepted"
        }
        (OracleOutcome::Error { .. }, CandidateOutcome::Rejected { .. }) => "both_rejected",
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn preserves_duplicate_members_numbers_and_scalar_units() {
        let candidate = parse_candidate(
            br#" {"a":-0.00e+001,"\u0061":1e400,"music":"\uD834\uDD1E"} "#,
            Limits::default(),
        );
        assert_eq!(
            candidate,
            CandidateOutcome::Accepted(WireValue::Object(vec![
                (vec![97], WireValue::Number(b"-0.00e+001".to_vec())),
                (vec![97], WireValue::Number(b"1e400".to_vec())),
                (
                    "music".encode_utf16().collect(),
                    WireValue::String(vec![0xd834, 0xdd1e])
                ),
            ]))
        );
    }
    #[test]
    fn strings_with_private_number_key_are_normal_objects() {
        let candidate = parse_candidate(
            br#"{"$serde_json::private::Number":"abc"}"#,
            Limits::default(),
        );
        assert!(matches!(
            candidate,
            CandidateOutcome::Accepted(WireValue::Object(_))
        ));
    }
    #[test]
    fn candidate_rejects_malformed_and_unpaired_scalar_strings() {
        for bytes in [
            b"01".as_slice(),
            b"true false",
            b"[1,]",
            b"{\"a\":}",
            br#""\uD800""#,
        ] {
            assert!(
                matches!(
                    parse_candidate(bytes, Limits::default()),
                    CandidateOutcome::Rejected { .. }
                ),
                "{bytes:?}"
            );
        }
    }
    #[test]
    fn candidate_limits_are_distinct() {
        assert_eq!(
            parse_candidate(
                b"123",
                Limits {
                    max_number_bytes: 2,
                    ..Limits::default()
                }
            ),
            CandidateOutcome::Limit { resource: "number" }
        );
        assert_eq!(
            parse_candidate(
                b"[null]",
                Limits {
                    max_nodes: 1,
                    ..Limits::default()
                }
            ),
            CandidateOutcome::Limit { resource: "nodes" }
        );
        assert_eq!(
            parse_candidate(
                br#""ab""#,
                Limits {
                    max_units: 1,
                    ..Limits::default()
                }
            ),
            CandidateOutcome::Limit { resource: "units" }
        );
        let deep = format!("{}null{}", "[".repeat(1000), "]".repeat(1000));
        assert_eq!(
            parse_candidate(deep.as_bytes(), Limits::default()),
            CandidateOutcome::Limit { resource: "depth" }
        );
        assert!(matches!(
            parse_candidate(br#""[[[[""#, Limits::default()),
            CandidateOutcome::Accepted(_)
        ));
    }
    #[test]
    fn protocol_accepts_exact_response_and_checks_offsets() {
        assert_eq!(
            parse_response(b"VJ1\tok\t00\n", 4, Limits::default()).unwrap(),
            OracleOutcome::Accepted(WireValue::Null)
        );
        assert_eq!(
            parse_response(b"VJ1\terr\tutf8\t1\n", 4, Limits::default()).unwrap(),
            OracleOutcome::Error {
                code: "utf8".into(),
                offset: 1
            }
        );
        for frame in [
            b"VJ2\tok\t00".as_slice(),
            b"VJ1\tok\t0",
            b"VJ1\tok\t0000",
            b"VJ1\tok\t00\nextra",
            b"VJ1\terr\tsyntax\t5",
            b"VJ1\terr\tsyntax\t-1",
            b"VJ1\terr\twrong\t0",
            b"VJ1\terr\tlimit_depth\t0",
        ] {
            assert!(
                matches!(
                    parse_response(frame, 4, Limits::default()),
                    Err(OracleFailure::Protocol(_))
                ),
                "{frame:?}"
            );
        }
        assert!(matches!(
            parse_response(
                b"VJ1\tok\t00",
                4,
                Limits {
                    max_bytes: 0,
                    ..Limits::default()
                }
            ),
            Err(OracleFailure::WireLimit(_))
        ));
    }
    #[test]
    fn classifiers_do_not_invent_bug_or_proof_claims() {
        let lone = OracleOutcome::Accepted(WireValue::String(vec![0xd800]));
        let rejection = CandidateOutcome::Rejected {
            category: "Syntax".into(),
            line: 1,
            column: 8,
        };
        assert_eq!(classify(&lone, &rejection), "scalar_profile_difference");
        assert_eq!(
            classify(
                &OracleOutcome::Error {
                    code: "limit".into(),
                    offset: 0
                },
                &rejection
            ),
            "oracle_limit"
        );
        assert_eq!(
            classify(
                &OracleOutcome::Error {
                    code: "transport".into(),
                    offset: 0
                },
                &rejection
            ),
            "oracle_infrastructure_failure"
        );
        assert_eq!(
            classify(
                &OracleOutcome::Accepted(WireValue::Null),
                &CandidateOutcome::Accepted(WireValue::Bool(false))
            ),
            "semantic_discrepancy"
        );
    }
}

#[cfg(all(test, unix))]
mod lifecycle_tests {
    use super::*;
    use std::cell::RefCell;
    use std::collections::VecDeque;

    struct ProcessFixture {
        events: RefCell<Vec<&'static str>>,
        observations: RefCell<VecDeque<Result<Option<ChildExit>, rustix::io::Errno>>>,
        group_error: Option<rustix::io::Errno>,
        reap_result: Result<bool, rustix::io::Errno>,
    }

    impl ProcessFixture {
        fn exited() -> Self {
            Self {
                events: RefCell::new(Vec::new()),
                observations: RefCell::new(VecDeque::from([Ok(Some(ChildExit { code: Some(0) }))])),
                group_error: None,
                reap_result: Ok(true),
            }
        }
    }

    impl ProcessControl for ProcessFixture {
        fn observe(&self) -> std::io::Result<Option<ChildExit>> {
            self.events.borrow_mut().push("observe-without-reaping");
            self.observations
                .borrow_mut()
                .pop_front()
                .expect("unexpected ownership observation")
                .map_err(Into::into)
        }
        fn signal_group(&mut self) -> std::io::Result<()> {
            assert!(!self.events.borrow().contains(&"reap"));
            self.events.borrow_mut().push("signal-group");
            self.group_error.map_or(Ok(()), |error| Err(error.into()))
        }
        fn kill_direct(&mut self) -> std::io::Result<()> {
            assert!(!self.events.borrow().contains(&"reap"));
            self.events.borrow_mut().push("kill-direct");
            Ok(())
        }
        fn reap(&mut self) -> std::io::Result<bool> {
            assert!(self.events.borrow().contains(&"observe-without-reaping"));
            self.events.borrow_mut().push("reap");
            self.reap_result.map_err(Into::into)
        }
    }

    #[test]
    fn completed_exchange_reaps_without_any_group_or_direct_signal() {
        let mut process = ProcessFixture::exited();
        cleanup_process(&mut process, CleanupMode::CompletedExchange, Duration::ZERO).unwrap();
        assert_eq!(
            *process.events.borrow(),
            ["observe-without-reaping", "reap"]
        );
    }

    #[test]
    fn incomplete_child_cannot_take_completed_exchange_cleanup() {
        let mut process = ProcessFixture::exited();
        *process.observations.borrow_mut() = VecDeque::from([Ok(None)]);
        assert!(
            matches!(cleanup_process(&mut process, CleanupMode::CompletedExchange, Duration::ZERO),
            Err(OracleFailure::Cleanup(detail)) if detail.contains("no waitable successful child exit"))
        );
        assert_eq!(*process.events.borrow(), ["observe-without-reaping"]);
    }

    #[test]
    fn all_signals_precede_reaping_even_when_exit_is_already_observed() {
        let mut process = ProcessFixture::exited();
        cleanup_process(&mut process, CleanupMode::Stop, Duration::ZERO).unwrap();
        assert_eq!(
            *process.events.borrow(),
            [
                "observe-without-reaping",
                "signal-group",
                "kill-direct",
                "reap"
            ]
        );
    }

    #[test]
    fn lost_waitable_identity_never_signals_a_numeric_pid() {
        let mut process = ProcessFixture::exited();
        *process.observations.borrow_mut() = VecDeque::from([Err(rustix::io::Errno::CHILD)]);
        let result = cleanup_process(&mut process, CleanupMode::Stop, Duration::ZERO);
        assert!(matches!(result, Err(OracleFailure::Cleanup(detail)) if
            detail.contains("waitable child ownership not established") && detail.ends_with("no signals sent")));
        assert_eq!(*process.events.borrow(), ["observe-without-reaping"]);
    }

    #[test]
    fn interrupted_ownership_observation_cannot_outlive_cleanup_budget() {
        let mut process = ProcessFixture::exited();
        *process.observations.borrow_mut() = VecDeque::from([Err(rustix::io::Errno::INTR)]);
        assert!(matches!(
            cleanup_process(&mut process, CleanupMode::Stop, Duration::ZERO),
            Err(OracleFailure::Cleanup(detail)) if detail.ends_with("no signals sent")
        ));
        assert_eq!(*process.events.borrow(), ["observe-without-reaping"]);
    }

    #[test]
    fn group_signal_failure_retains_uncertainty_after_direct_reap() {
        let mut process = ProcessFixture::exited();
        process.group_error = Some(rustix::io::Errno::PERM);
        let result = cleanup_process(&mut process, CleanupMode::Stop, Duration::ZERO);
        assert!(matches!(result, Err(OracleFailure::Cleanup(detail)) if
            detail.contains("process-group termination not established") &&
            detail.ends_with("direct child reaped after bounded fallback")));
        assert_eq!(
            *process.events.borrow(),
            [
                "observe-without-reaping",
                "signal-group",
                "kill-direct",
                "reap"
            ]
        );
    }

    #[test]
    fn absent_group_still_requires_direct_reap() {
        let mut process = ProcessFixture::exited();
        process.group_error = Some(rustix::io::Errno::SRCH);
        process.reap_result = Ok(false);
        assert!(
            matches!(cleanup_process(&mut process, CleanupMode::Stop, Duration::ZERO),
            Err(OracleFailure::Cleanup(detail)) if detail.contains("termination not observed"))
        );
    }

    #[test]
    fn cleanup_uncertainty_suppresses_success_and_preserves_primary_failure() {
        let mut process = ProcessFixture::exited();
        process.reap_result = Ok(false);
        let cleanup = cleanup_process(&mut process, CleanupMode::Stop, Duration::ZERO);
        let result = finish_run(Err(OracleFailure::OutputLimit("stdout")), cleanup);
        assert!(
            matches!(result, Err(OracleFailure::WithCleanup { primary, cleanup }) if
            *primary == OracleFailure::OutputLimit("stdout") &&
            matches!(*cleanup, OracleFailure::Cleanup(_)))
        );

        let run = OracleRun {
            outcome: OracleOutcome::Accepted(WireValue::Null),
            stderr_bytes: 0,
        };
        assert!(matches!(
            finish_run(Ok(run), Err(OracleFailure::Cleanup("unobserved".into()))),
            Err(OracleFailure::Cleanup(_))
        ));
    }

    #[test]
    fn real_completion_observation_keeps_status_waitable_until_cleanup() {
        if !HAS_WAITID {
            return;
        }
        use std::os::unix::process::CommandExt;
        let mut child = Command::new("/bin/sh")
            .args(["-c", "exit 0"])
            .env_clear()
            .stdin(Stdio::null())
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .process_group(0)
            .spawn()
            .unwrap();
        let deadline = Instant::now() + Duration::from_secs(2);
        let observation = loop {
            match observe_child_exit(&child) {
                Ok(Some(status)) => break Ok(status),
                Ok(None) if Instant::now() < deadline => {
                    std::thread::sleep(Duration::from_millis(2));
                }
                Ok(None) => break Err(std::io::Error::other("fixture exit not observed")),
                Err(error) => break Err(error),
            }
        };
        let repeated = observe_child_exit(&child);
        // Cleanup is always attempted before assertions, including probe failure.
        let mode = if matches!(repeated, Ok(Some(ChildExit { code: Some(0) }))) {
            CleanupMode::CompletedExchange
        } else {
            CleanupMode::Stop
        };
        let cleanup = cleanup_process(&mut child, mode, Duration::from_millis(250));
        assert_eq!(observation.unwrap(), ChildExit { code: Some(0) });
        assert_eq!(repeated.unwrap(), Some(ChildExit { code: Some(0) }));
        cleanup.unwrap();
        // Child's cached reaped status remains available with no later signal.
        assert_eq!(child.try_wait().unwrap().unwrap().code(), Some(0));
    }
}
