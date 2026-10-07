use json_diff::{
    classify, parse_candidate, run_oracle, CandidateOutcome, OracleFailure, OracleOutcome,
    INPUT_LIMIT, PROFILE,
};
use json_wire::{hex_decode, HexError, Limits};
use std::io::Read;
use std::path::PathBuf;
use std::time::Duration;

fn usage() -> ! {
    eprintln!("Usage: verified-json-diff --oracle PATH [--input FILE | --hex HEX] [--timeout-ms 1..60000]\nWithout --input/--hex, reads JSON bytes from stdin. Local comparison only; no reporter.");
    std::process::exit(64)
}
#[derive(Debug)]
enum InputFailure {
    Limit,
    Io(String),
    Hex(HexError),
    NonUtf8Hex,
}
fn bounded_read(mut reader: impl Read) -> Result<Vec<u8>, InputFailure> {
    let mut bytes = Vec::new();
    reader
        .by_ref()
        .take((INPUT_LIMIT + 1) as u64)
        .read_to_end(&mut bytes)
        .map_err(|error| InputFailure::Io(error.to_string()))?;
    if bytes.len() > INPUT_LIMIT {
        return Err(InputFailure::Limit);
    }
    Ok(bytes)
}
fn main() {
    let mut args = std::env::args_os().skip(1);
    let mut oracle = None;
    let mut input = None;
    let mut hex = None;
    let mut timeout_ms = 2000u64;
    while let Some(arg) = args.next() {
        match arg.to_str() {
            Some("--oracle") if oracle.is_none() => {
                oracle = Some(PathBuf::from(args.next().unwrap_or_else(|| usage())))
            }
            Some("--input") if input.is_none() && hex.is_none() => {
                input = Some(PathBuf::from(args.next().unwrap_or_else(|| usage())))
            }
            Some("--hex") if input.is_none() && hex.is_none() => {
                hex = Some(args.next().unwrap_or_else(|| usage()))
            }
            Some("--timeout-ms") => {
                let value = args.next().unwrap_or_else(|| usage());
                timeout_ms = value
                    .to_str()
                    .and_then(|text| text.parse().ok())
                    .filter(|&n| (1..=60000).contains(&n))
                    .unwrap_or_else(|| usage());
            }
            Some("--help") => {
                println!("Usage: verified-json-diff --oracle PATH [--input FILE | --hex HEX] [--timeout-ms 1..60000]\nWithout --input/--hex, reads JSON bytes from stdin. Local comparison only; no reporter.");
                return;
            }
            _ => usage(),
        }
    }
    let oracle = oracle.unwrap_or_else(|| usage());
    let bytes = if let Some(hex) = hex {
        hex.to_str()
            .ok_or(InputFailure::NonUtf8Hex)
            .and_then(|hex| hex_decode(hex.as_bytes(), INPUT_LIMIT).map_err(InputFailure::Hex))
    } else if let Some(input) = input {
        std::fs::File::open(input)
            .map_err(|error| InputFailure::Io(error.to_string()))
            .and_then(bounded_read)
    } else {
        bounded_read(std::io::stdin().lock())
    };
    let bytes = match bytes {
        Ok(bytes) => bytes,
        Err(error) => {
            let (classification, exit, detail) = match error {
                InputFailure::Limit | InputFailure::Hex(HexError::Limit) => {
                    ("input_limit", 4, "input byte cap exceeded".into())
                }
                InputFailure::Io(detail) => ("input_infrastructure_failure", 3, detail),
                InputFailure::Hex(HexError::Allocation) => (
                    "input_infrastructure_failure",
                    3,
                    "hex allocation failed".into(),
                ),
                other => ("input_encoding_failure", 64, format!("{other:?}")),
            };
            println!(
                "{}",
                serde_json::json!({"classification":classification,"detail":detail,"proof_claim":false})
            );
            std::process::exit(exit);
        }
    };
    let limits = Limits::default();
    let candidate = parse_candidate(&bytes, limits);
    let run = match run_oracle(&oracle, &bytes, Duration::from_millis(timeout_ms), limits) {
        Ok(run) => run,
        Err(error) => {
            let class = match &error {
                OracleFailure::WireLimit(_) | OracleFailure::OutputLimit(_) => {
                    "infrastructure_limit"
                }
                OracleFailure::Protocol(_) => "protocol_failure",
                _ => "infrastructure_failure",
            };
            println!(
                "{}",
                serde_json::json!({"classification":class,"detail":format!("{error:?}"),"candidate_profile":PROFILE,"input_bytes":bytes.len(),"proof_claim":false})
            );
            std::process::exit(if class == "infrastructure_limit" {
                4
            } else {
                3
            });
        }
    };
    let classification = classify(&run.outcome, &candidate);
    let oracle_description = match &run.outcome {
        OracleOutcome::Accepted(_) => serde_json::json!({"status":"accepted"}),
        OracleOutcome::Error { code, offset } => {
            serde_json::json!({"status":"error","code":code,"offset":offset})
        }
    };
    let candidate_description = match &candidate {
        CandidateOutcome::Accepted(_) => serde_json::json!({"status":"accepted"}),
        CandidateOutcome::Rejected {
            category,
            line,
            column,
        } => {
            serde_json::json!({"status":"rejected","category":category,"line":line,"column":column})
        }
        CandidateOutcome::Limit { resource } => {
            serde_json::json!({"status":"limit","resource":resource})
        }
    };
    println!(
        "{}",
        serde_json::json!({
            "classification":classification,
            "candidate_profile":PROFILE,
            "oracle":oracle_description,
            "candidate":candidate_description,
            "input_bytes":bytes.len(),
            "oracle_stderr_bytes":run.stderr_bytes,
            "numeric_conversion":false,
            "proof_claim":false,
        })
    );
    let exit = match classification {
        "agreement" | "both_rejected" => 0,
        "oracle_limit" | "candidate_limit" => 4,
        "scalar_profile_difference" | "oracle_unsupported" => 5,
        "oracle_infrastructure_failure" => 3,
        _ => 2,
    };
    std::process::exit(exit);
}
