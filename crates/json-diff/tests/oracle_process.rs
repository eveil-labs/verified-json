#![cfg(unix)]
use json_diff::{run_oracle, OracleFailure, OracleOutcome};
use json_wire::{encode, hex_encode, Limits, WireValue};
use std::os::unix::fs::PermissionsExt;
use std::path::PathBuf;
use std::process::Command;
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::Duration;

static NEXT: AtomicU64 = AtomicU64::new(0);
fn script(body: &str) -> PathBuf {
    let base = std::env::var_os("VERIFIED_JSON_TEST_WORK")
        .expect("VERIFIED_JSON_TEST_WORK must name allocated central test scratch");
    let directory = PathBuf::from(base).join(format!(
        "oracle-{}-{}",
        std::process::id(),
        NEXT.fetch_add(1, Ordering::Relaxed)
    ));
    std::fs::create_dir_all(&directory).unwrap();
    let path = directory.join("oracle.sh");
    std::fs::write(&path, format!("#!/bin/sh\n{body}\n")).unwrap();
    std::fs::set_permissions(&path, std::fs::Permissions::from_mode(0o700)).unwrap();
    path
}
fn response(value: &WireValue) -> String {
    format!(
        "VJ1\tok\t{}",
        hex_encode(&encode(value, Limits::default()).unwrap())
    )
}
fn observe_failure(failure: OracleFailure) -> OracleFailure {
    if let OracleFailure::WithCleanup { cleanup, .. } = &failure {
        eprintln!("separate cleanup observation: {cleanup:?}");
        // A group-signal limitation may be retained, but unobserved direct-child
        // cleanup must not make a lifecycle fixture pass.
        assert!(matches!(cleanup.as_ref(), OracleFailure::Cleanup(detail) if
            detail.ends_with("direct child reaped after bounded fallback")));
    }
    failure
}
#[test]
fn subprocess_obeys_hex_request_and_response_contract() {
    let path = script(
        "IFS= read -r request\n[ \"$request\" = '6e756c6c' ] || exit 7\nprintf 'VJ1\\tok\\t00\\n'",
    );
    let run = run_oracle(&path, b"null", Duration::from_secs(2), Limits::default()).unwrap();
    assert_eq!(run.outcome, OracleOutcome::Accepted(WireValue::Null));
    assert_eq!(run.stderr_bytes, 0);
}
#[test]
fn timeout_covers_an_oracle_not_reading_stdin() {
    let path = script("/bin/sleep 5");
    let input = vec![b' '; 256 * 1024];
    assert_eq!(
        observe_failure(
            run_oracle(&path, &input, Duration::from_millis(40), Limits::default()).unwrap_err()
        )
        .primary(),
        &OracleFailure::Timeout
    );
}
#[test]
fn stdout_stderr_and_exit_failures_are_not_syntax_results() {
    let path = script("cat >/dev/null\nprintf 'diagnostic\\nVJ1\\tok\\t00\\n'");
    assert!(matches!(
        observe_failure(
            run_oracle(&path, b"null", Duration::from_secs(2), Limits::default()).unwrap_err()
        )
        .primary(),
        OracleFailure::Protocol(_)
    ));
    let path = script("cat >/dev/null\nwhile :; do printf '0123456789abcdef'; done");
    assert_eq!(
        observe_failure(
            run_oracle(
                &path,
                b"null",
                Duration::from_secs(2),
                Limits {
                    max_bytes: 1,
                    ..Limits::default()
                }
            )
            .unwrap_err()
        )
        .primary(),
        &OracleFailure::OutputLimit("stdout")
    );
    let path = script("cat >/dev/null\nwhile :; do printf '0123456789abcdef' >&2; done");
    assert_eq!(
        observe_failure(
            run_oracle(&path, b"null", Duration::from_secs(2), Limits::default()).unwrap_err()
        )
        .primary(),
        &OracleFailure::OutputLimit("stderr")
    );
    let path = script("cat >/dev/null\nexit 7");
    assert_eq!(
        observe_failure(
            run_oracle(&path, b"null", Duration::from_secs(2), Limits::default()).unwrap_err()
        )
        .primary(),
        &OracleFailure::Exit(Some(7))
    );
}
#[test]
fn cli_detects_agreement_seeded_discrepancy_and_scalar_profile_gap() {
    for (input, expected, class, exit) in [
        ("null", WireValue::Null, "agreement", 0),
        ("null", WireValue::Bool(false), "semantic_discrepancy", 2),
        (
            r#""\uD800""#,
            WireValue::String(vec![0xd800]),
            "scalar_profile_difference",
            5,
        ),
    ] {
        let line = response(&expected);
        let path = script(&format!("cat >/dev/null\nprintf '%s\\n' '{line}'"));
        let output = Command::new(env!("CARGO_BIN_EXE_verified-json-diff"))
            .args([
                "--oracle",
                path.to_str().unwrap(),
                "--hex",
                &hex_encode(input.as_bytes()),
            ])
            .output()
            .unwrap();
        assert_eq!(
            output.status.code(),
            Some(exit),
            "{}",
            String::from_utf8_lossy(&output.stderr)
        );
        let json: serde_json::Value = serde_json::from_slice(&output.stdout).unwrap();
        assert_eq!(json["classification"], class);
        assert_eq!(json["proof_claim"], false);
        assert_eq!(json["numeric_conversion"], false);
    }
}
#[test]
fn process_does_not_inherit_arbitrary_environment() {
    let path = script(
        "cat >/dev/null\n[ -z \"$VJ_SENTINEL_SECRET\" ] || exit 7\nprintf 'VJ1\\tok\\t00\\n'",
    );
    let output = Command::new(env!("CARGO_BIN_EXE_verified-json-diff"))
        .env("VJ_SENTINEL_SECRET", "public-synthetic-sentinel")
        .args(["--oracle", path.to_str().unwrap(), "--hex", "6e756c6c"])
        .output()
        .unwrap();
    assert!(output.status.success());
}

#[test]
fn escaped_pipe_holder_cannot_leave_io_threads_or_block_the_call() {
    // A trusted synthetic peer deliberately leaves the process group. This tests
    // bounded nonblocking caller I/O, not an adversarial containment guarantee.
    for _ in 0..3 {
        let path = script("cat >/dev/null\nexec /usr/bin/python3 -S \"$0.py\"");
        let python = path.with_extension("sh.py");
        std::fs::write(&python, "import os, time\npid = os.fork()\nif pid == 0:\n    os.setsid()\n    with open(__file__ + '.ready', 'w') as f:\n        f.write('ready')\n    deadline = time.monotonic() + 5\n    while time.monotonic() < deadline and not os.path.exists(__file__ + '.release'):\n        time.sleep(0.005)\n    with open(__file__ + '.done', 'w') as f:\n        f.write('done')\n    os._exit(0)\nos._exit(0)\n").unwrap();
        let started = std::time::Instant::now();
        let result = run_oracle(&path, b"null", Duration::from_secs(2), Limits::default());
        let elapsed = started.elapsed();
        // Release the owned detached fixture without signaling an unowned raw
        // PID, which could itself have expired/recycled if this test was paused.
        // The fixture also self-expires if the test process is interrupted.
        std::fs::write(python.with_extension("py.release"), b"release").unwrap();
        let done = python.with_extension("py.done");
        let release_deadline = std::time::Instant::now() + Duration::from_secs(2);
        while !done.is_file() && std::time::Instant::now() < release_deadline {
            std::thread::sleep(Duration::from_millis(5));
        }
        assert!(
            python.with_extension("py.ready").is_file(),
            "escaped fixture did not start; result={result:?}"
        );
        assert!(
            done.is_file(),
            "escaped fixture did not finish after release; result={result:?}"
        );
        assert_eq!(
            observe_failure(result.unwrap_err()).primary(),
            &OracleFailure::Timeout
        );
        assert!(elapsed < Duration::from_secs(4));
    }
}

#[test]
fn exited_leader_with_group_pipe_holder_still_obeys_timeout() {
    let path = script("cat >/dev/null\n/bin/sleep 3 &\nexit 0");
    let started = std::time::Instant::now();
    let result = run_oracle(&path, b"null", Duration::from_millis(80), Limits::default());
    assert_eq!(
        observe_failure(result.unwrap_err()).primary(),
        &OracleFailure::Timeout
    );
    assert!(started.elapsed() < Duration::from_secs(2));
}

#[test]
fn signal_termination_keeps_the_original_exit_category() {
    let path = script("cat >/dev/null\nkill -TERM $$");
    let result = run_oracle(&path, b"null", Duration::from_secs(2), Limits::default());
    assert_eq!(
        observe_failure(result.unwrap_err()).primary(),
        &OracleFailure::Exit(None)
    );
}
