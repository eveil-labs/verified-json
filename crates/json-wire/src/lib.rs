//! Candidate neutral codec. This native implementation is tested, not formally verified.
//! Wire strings are UTF-16 code units, including unpaired surrogates. Object members
//! remain an ordered sequence. Number tokens retain their exact ASCII spelling.

use std::fmt;

pub const HARD_MAX_DEPTH: usize = 256;

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum WireValue {
    Null,
    Bool(bool),
    Number(Vec<u8>),
    String(Vec<u16>),
    Array(Vec<WireValue>),
    Object(Vec<(Vec<u16>, WireValue)>),
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Limits {
    pub max_bytes: usize,
    /// Root has depth zero. The native recursion ceiling is independently capped.
    pub max_depth: usize,
    /// Charges one per value and one additional unit per object member.
    pub max_nodes: usize,
    /// Total string/key units, rather than a separate allowance per string.
    pub max_units: usize,
    pub max_number_bytes: usize,
}

impl Default for Limits {
    fn default() -> Self {
        Self {
            max_bytes: 8 * 1024 * 1024,
            max_depth: 128,
            max_nodes: 100_000,
            max_units: 2 * 1024 * 1024,
            max_number_bytes: 4096,
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ErrorKind {
    Truncated,
    InvalidTag(u8),
    InvalidNumber,
    TrailingBytes,
    LimitBytes,
    LimitDepth,
    LimitNodes,
    LimitUnits,
    LimitNumber,
    InvalidLimits,
    Allocation,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct CodecError {
    pub kind: ErrorKind,
    pub offset: usize,
}

impl fmt::Display for CodecError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{:?} at wire byte {}", self.kind, self.offset)
    }
}
impl std::error::Error for CodecError {}

impl ErrorKind {
    pub fn is_limit(self) -> bool {
        matches!(
            self,
            Self::LimitBytes
                | Self::LimitDepth
                | Self::LimitNodes
                | Self::LimitUnits
                | Self::LimitNumber
        )
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum HexError {
    OddLength,
    InvalidDigit(usize),
    Limit,
    Allocation,
}

pub fn hex_encode(bytes: &[u8]) -> String {
    const DIGITS: &[u8; 16] = b"0123456789abcdef";
    let mut out = String::with_capacity(bytes.len().saturating_mul(2));
    for &byte in bytes {
        out.push(DIGITS[(byte >> 4) as usize] as char);
        out.push(DIGITS[(byte & 15) as usize] as char);
    }
    out
}

pub fn hex_decode(text: &[u8], max_bytes: usize) -> Result<Vec<u8>, HexError> {
    if !text.len().is_multiple_of(2) {
        return Err(HexError::OddLength);
    }
    let len = text.len() / 2;
    if len > max_bytes {
        return Err(HexError::Limit);
    }
    let mut out = Vec::new();
    out.try_reserve_exact(len)
        .map_err(|_| HexError::Allocation)?;
    fn digit(b: u8) -> Option<u8> {
        match b {
            b'0'..=b'9' => Some(b - b'0'),
            b'a'..=b'f' => Some(b - b'a' + 10),
            b'A'..=b'F' => Some(b - b'A' + 10),
            _ => None,
        }
    }
    for (i, pair) in text.chunks_exact(2).enumerate() {
        let hi = digit(pair[0]).ok_or(HexError::InvalidDigit(i * 2))?;
        let lo = digit(pair[1]).ok_or(HexError::InvalidDigit(i * 2 + 1))?;
        out.push(hi * 16 + lo);
    }
    Ok(out)
}

/// Independent syntactic check used only for neutral number fields, not conversion.
pub fn valid_number_token(bytes: &[u8]) -> bool {
    let mut i = 0;
    if bytes.get(i) == Some(&b'-') {
        i += 1;
    }
    match bytes.get(i) {
        Some(b'0') => i += 1,
        Some(b'1'..=b'9') => {
            i += 1;
            while matches!(bytes.get(i), Some(b'0'..=b'9')) {
                i += 1;
            }
        }
        _ => return false,
    }
    if bytes.get(i) == Some(&b'.') {
        i += 1;
        let start = i;
        while matches!(bytes.get(i), Some(b'0'..=b'9')) {
            i += 1;
        }
        if i == start {
            return false;
        }
    }
    if matches!(bytes.get(i), Some(b'e' | b'E')) {
        i += 1;
        if matches!(bytes.get(i), Some(b'+' | b'-')) {
            i += 1;
        }
        let start = i;
        while matches!(bytes.get(i), Some(b'0'..=b'9')) {
            i += 1;
        }
        if i == start {
            return false;
        }
    }
    i == bytes.len()
}

struct Budget {
    limits: Limits,
    nodes: usize,
    units: usize,
}

impl Budget {
    fn new(limits: Limits) -> Result<Self, CodecError> {
        if limits.max_depth > HARD_MAX_DEPTH {
            return Err(CodecError {
                kind: ErrorKind::InvalidLimits,
                offset: 0,
            });
        }
        Ok(Self {
            limits,
            nodes: 0,
            units: 0,
        })
    }
    fn charge_nodes(&mut self, amount: usize, offset: usize) -> Result<(), CodecError> {
        self.nodes = self
            .nodes
            .checked_add(amount)
            .filter(|&n| n <= self.limits.max_nodes)
            .ok_or(CodecError {
                kind: ErrorKind::LimitNodes,
                offset,
            })?;
        Ok(())
    }
    fn charge_units(&mut self, amount: usize, offset: usize) -> Result<(), CodecError> {
        self.units = self
            .units
            .checked_add(amount)
            .filter(|&n| n <= self.limits.max_units)
            .ok_or(CodecError {
                kind: ErrorKind::LimitUnits,
                offset,
            })?;
        Ok(())
    }
    fn depth(&self, depth: usize, offset: usize) -> Result<(), CodecError> {
        if depth > self.limits.max_depth {
            return Err(CodecError {
                kind: ErrorKind::LimitDepth,
                offset,
            });
        }
        Ok(())
    }
}

struct Decoder<'a> {
    bytes: &'a [u8],
    pos: usize,
    budget: Budget,
}

impl<'a> Decoder<'a> {
    fn take(&mut self, count: usize) -> Result<&'a [u8], CodecError> {
        let end = self
            .pos
            .checked_add(count)
            .filter(|&end| end <= self.bytes.len())
            .ok_or(CodecError {
                kind: ErrorKind::Truncated,
                offset: self.pos,
            })?;
        let out = &self.bytes[self.pos..end];
        self.pos = end;
        Ok(out)
    }
    fn count(&mut self) -> Result<usize, CodecError> {
        let bytes = self.take(4)?;
        Ok(u32::from_le_bytes([bytes[0], bytes[1], bytes[2], bytes[3]]) as usize)
    }
    fn units(&mut self) -> Result<Vec<u16>, CodecError> {
        let count = self.count()?;
        self.budget.charge_units(count, self.pos)?;
        let size = count.checked_mul(2).ok_or(CodecError {
            kind: ErrorKind::Truncated,
            offset: self.pos,
        })?;
        let bytes = self.take(size)?;
        let mut units = Vec::new();
        units.try_reserve_exact(count).map_err(|_| CodecError {
            kind: ErrorKind::Allocation,
            offset: self.pos,
        })?;
        for b in bytes.chunks_exact(2) {
            units.push(u16::from_le_bytes([b[0], b[1]]));
        }
        Ok(units)
    }
    fn value(&mut self, depth: usize) -> Result<WireValue, CodecError> {
        self.budget.depth(depth, self.pos)?;
        self.budget.charge_nodes(1, self.pos)?;
        let tag = self.take(1)?[0];
        match tag {
            0 => Ok(WireValue::Null),
            1 => Ok(WireValue::Bool(false)),
            2 => Ok(WireValue::Bool(true)),
            3 => {
                let count = self.count()?;
                if count > self.budget.limits.max_number_bytes {
                    return Err(CodecError {
                        kind: ErrorKind::LimitNumber,
                        offset: self.pos,
                    });
                }
                let bytes = self.take(count)?;
                if !valid_number_token(bytes) {
                    return Err(CodecError {
                        kind: ErrorKind::InvalidNumber,
                        offset: self.pos - count,
                    });
                }
                Ok(WireValue::Number(bytes.to_vec()))
            }
            4 => Ok(WireValue::String(self.units()?)),
            5 => {
                let count = self.count()?;
                if count
                    > self
                        .budget
                        .limits
                        .max_nodes
                        .saturating_sub(self.budget.nodes)
                {
                    return Err(CodecError {
                        kind: ErrorKind::LimitNodes,
                        offset: self.pos,
                    });
                }
                if count > self.bytes.len() - self.pos {
                    return Err(CodecError {
                        kind: ErrorKind::Truncated,
                        offset: self.pos,
                    });
                }
                let mut values = Vec::new();
                values.try_reserve_exact(count).map_err(|_| CodecError {
                    kind: ErrorKind::Allocation,
                    offset: self.pos,
                })?;
                for _ in 0..count {
                    values.push(self.value(depth + 1)?);
                }
                Ok(WireValue::Array(values))
            }
            6 => {
                let count = self.count()?;
                self.budget.charge_nodes(count, self.pos)?;
                if count
                    > self
                        .budget
                        .limits
                        .max_nodes
                        .saturating_sub(self.budget.nodes)
                {
                    return Err(CodecError {
                        kind: ErrorKind::LimitNodes,
                        offset: self.pos,
                    });
                }
                if count > (self.bytes.len() - self.pos) / 5 {
                    return Err(CodecError {
                        kind: ErrorKind::Truncated,
                        offset: self.pos,
                    });
                }
                let mut members = Vec::new();
                members.try_reserve_exact(count).map_err(|_| CodecError {
                    kind: ErrorKind::Allocation,
                    offset: self.pos,
                })?;
                for _ in 0..count {
                    let key = self.units()?;
                    members.push((key, self.value(depth + 1)?));
                }
                Ok(WireValue::Object(members))
            }
            other => Err(CodecError {
                kind: ErrorKind::InvalidTag(other),
                offset: self.pos - 1,
            }),
        }
    }
}

pub fn decode(bytes: &[u8], limits: Limits) -> Result<WireValue, CodecError> {
    let budget = Budget::new(limits)?;
    if bytes.len() > limits.max_bytes {
        return Err(CodecError {
            kind: ErrorKind::LimitBytes,
            offset: 0,
        });
    }
    let mut decoder = Decoder {
        bytes,
        pos: 0,
        budget,
    };
    let value = decoder.value(0)?;
    if decoder.pos != bytes.len() {
        return Err(CodecError {
            kind: ErrorKind::TrailingBytes,
            offset: decoder.pos,
        });
    }
    Ok(value)
}

struct Encoder {
    bytes: Vec<u8>,
    budget: Budget,
}
impl Encoder {
    fn put(&mut self, bytes: &[u8]) -> Result<(), CodecError> {
        self.bytes
            .len()
            .checked_add(bytes.len())
            .filter(|&n| n <= self.budget.limits.max_bytes)
            .ok_or(CodecError {
                kind: ErrorKind::LimitBytes,
                offset: self.bytes.len(),
            })?;
        self.bytes
            .try_reserve(bytes.len())
            .map_err(|_| CodecError {
                kind: ErrorKind::Allocation,
                offset: self.bytes.len(),
            })?;
        self.bytes.extend_from_slice(bytes);
        Ok(())
    }
    fn count(&mut self, count: usize) -> Result<(), CodecError> {
        let count = u32::try_from(count).map_err(|_| CodecError {
            kind: ErrorKind::LimitBytes,
            offset: self.bytes.len(),
        })?;
        self.put(&count.to_le_bytes())
    }
    fn units(&mut self, units: &[u16]) -> Result<(), CodecError> {
        self.budget.charge_units(units.len(), self.bytes.len())?;
        self.count(units.len())?;
        for unit in units {
            self.put(&unit.to_le_bytes())?;
        }
        Ok(())
    }
    fn value(&mut self, value: &WireValue, depth: usize) -> Result<(), CodecError> {
        self.budget.depth(depth, self.bytes.len())?;
        self.budget.charge_nodes(1, self.bytes.len())?;
        match value {
            WireValue::Null => self.put(&[0]),
            WireValue::Bool(false) => self.put(&[1]),
            WireValue::Bool(true) => self.put(&[2]),
            WireValue::Number(bytes) => {
                if bytes.len() > self.budget.limits.max_number_bytes {
                    return Err(CodecError {
                        kind: ErrorKind::LimitNumber,
                        offset: self.bytes.len(),
                    });
                }
                if !valid_number_token(bytes) {
                    return Err(CodecError {
                        kind: ErrorKind::InvalidNumber,
                        offset: self.bytes.len(),
                    });
                }
                self.put(&[3])?;
                self.count(bytes.len())?;
                self.put(bytes)
            }
            WireValue::String(units) => {
                self.put(&[4])?;
                self.units(units)
            }
            WireValue::Array(values) => {
                self.put(&[5])?;
                self.count(values.len())?;
                for value in values {
                    self.value(value, depth + 1)?;
                }
                Ok(())
            }
            WireValue::Object(members) => {
                self.budget.charge_nodes(members.len(), self.bytes.len())?;
                self.put(&[6])?;
                self.count(members.len())?;
                for (key, value) in members {
                    self.units(key)?;
                    self.value(value, depth + 1)?;
                }
                Ok(())
            }
        }
    }
}
pub fn encode(value: &WireValue, limits: Limits) -> Result<Vec<u8>, CodecError> {
    let mut encoder = Encoder {
        bytes: Vec::new(),
        budget: Budget::new(limits)?,
    };
    encoder.value(value, 0)?;
    Ok(encoder.bytes)
}

pub fn scalar_units(units: &[u16]) -> bool {
    std::char::decode_utf16(units.iter().copied()).all(|unit| unit.is_ok())
}
pub fn contains_non_scalar(value: &WireValue) -> bool {
    match value {
        WireValue::String(units) => !scalar_units(units),
        WireValue::Array(values) => values.iter().any(contains_non_scalar),
        WireValue::Object(members) => members
            .iter()
            .any(|(key, value)| !scalar_units(key) || contains_non_scalar(value)),
        _ => false,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    fn sample() -> WireValue {
        WireValue::Object(vec![
            (vec![0x61], WireValue::Number(b"-0.00e+001".to_vec())),
            (
                vec![0x61],
                WireValue::Array(vec![
                    WireValue::Null,
                    WireValue::Bool(false),
                    WireValue::Bool(true),
                ]),
            ),
            (
                vec![0xd800],
                WireValue::String(vec![0xd834, 0xdd1e, 0xdc00]),
            ),
        ])
    }
    #[test]
    fn exact_format_roundtrip() {
        let value = sample();
        let bytes = encode(&value, Limits::default()).unwrap();
        assert_eq!(decode(&bytes, Limits::default()).unwrap(), value);
        assert_eq!(&bytes[..5], &[6, 3, 0, 0, 0]);
        assert!(contains_non_scalar(&value));
        assert!(!contains_non_scalar(&WireValue::String(vec![
            0xd834, 0xdd1e
        ])));
    }
    #[test]
    fn every_truncated_prefix_fails() {
        let bytes = encode(&sample(), Limits::default()).unwrap();
        for len in 0..bytes.len() {
            assert!(
                decode(&bytes[..len], Limits::default()).is_err(),
                "prefix {len}"
            );
        }
    }
    #[test]
    fn trailing_bytes_and_tags_fail() {
        assert_eq!(
            decode(&[0, 0], Limits::default()).unwrap_err().kind,
            ErrorKind::TrailingBytes
        );
        assert_eq!(
            decode(&[255], Limits::default()).unwrap_err().kind,
            ErrorKind::InvalidTag(255)
        );
    }
    #[test]
    fn large_untrusted_counts_fail_before_allocating() {
        for tag in [3, 4, 5, 6] {
            let error = decode(&[tag, 255, 255, 255, 255], Limits::default()).unwrap_err();
            assert!(error.kind.is_limit(), "{tag}: {error}");
        }
    }
    #[test]
    fn explicit_budgets_apply_to_encode_and_decode() {
        let value = sample();
        let bytes = encode(&value, Limits::default()).unwrap();
        for limits in [
            Limits {
                max_bytes: 0,
                ..Limits::default()
            },
            Limits {
                max_depth: 0,
                ..Limits::default()
            },
            Limits {
                max_nodes: 2,
                ..Limits::default()
            },
            Limits {
                max_units: 1,
                ..Limits::default()
            },
            Limits {
                max_number_bytes: 1,
                ..Limits::default()
            },
        ] {
            assert!(encode(&value, limits).unwrap_err().kind.is_limit());
            assert!(decode(&bytes, limits).unwrap_err().kind.is_limit());
        }
    }
    #[test]
    fn total_units_and_member_nodes_are_charged() {
        let value = WireValue::Object(vec![(vec![97], WireValue::String(vec![98]))]);
        let bytes = encode(&value, Limits::default()).unwrap();
        assert_eq!(
            decode(
                &bytes,
                Limits {
                    max_nodes: 2,
                    ..Limits::default()
                }
            )
            .unwrap_err()
            .kind,
            ErrorKind::LimitNodes
        );
        assert_eq!(
            decode(
                &bytes,
                Limits {
                    max_units: 1,
                    ..Limits::default()
                }
            )
            .unwrap_err()
            .kind,
            ErrorKind::LimitUnits
        );
        assert!(decode(
            &bytes,
            Limits {
                max_nodes: 3,
                max_units: 2,
                ..Limits::default()
            }
        )
        .is_ok());
    }
    #[test]
    fn number_grammar_is_checked_without_numeric_conversion() {
        for token in ["0", "-0", "12", "-1.0", "1e999999", "1E-2", "0.00e+001"] {
            assert!(valid_number_token(token.as_bytes()), "{token}");
        }
        for token in [
            "", "-", "+1", "01", "-01", ".1", "1.", "1e", "NaN", "1 2", "∞",
        ] {
            assert!(!valid_number_token(token.as_bytes()), "{token}");
            assert_eq!(
                encode(
                    &WireValue::Number(token.as_bytes().to_vec()),
                    Limits::default()
                )
                .unwrap_err()
                .kind,
                ErrorKind::InvalidNumber
            );
        }
        assert_eq!(
            decode(&[3, 1, 0, 0, 0, b'x'], Limits::default())
                .unwrap_err()
                .kind,
            ErrorKind::InvalidNumber
        );
    }
    #[test]
    fn hex_is_bounded_and_strict() {
        assert_eq!(hex_decode(b"Aa00ff", 3).unwrap(), vec![170, 0, 255]);
        assert_eq!(hex_encode(&[170, 0, 255]), "aa00ff");
        assert_eq!(hex_decode(b"a", 3), Err(HexError::OddLength));
        assert_eq!(hex_decode(b"0x", 3), Err(HexError::InvalidDigit(1)));
        assert_eq!(hex_decode(b"0000", 1), Err(HexError::Limit));
    }
    #[test]
    fn invalid_native_depth_configuration_is_refused() {
        assert_eq!(
            decode(
                &[0],
                Limits {
                    max_depth: HARD_MAX_DEPTH + 1,
                    ..Limits::default()
                }
            )
            .unwrap_err()
            .kind,
            ErrorKind::InvalidLimits
        );
    }
    #[test]
    fn broad_deterministic_corpus_roundtrips() {
        let mut values = vec![
            WireValue::Null,
            WireValue::Bool(false),
            WireValue::Bool(true),
        ];
        for i in 0..128u16 {
            values.push(WireValue::String(vec![i, 0xd800 + i]));
            values.push(WireValue::Number(format!("-{i}.125e+2").into_bytes()));
        }
        for value in &values {
            for wrapper in [
                value.clone(),
                WireValue::Array(vec![value.clone()]),
                WireValue::Object(vec![(vec![0xd800], value.clone())]),
            ] {
                let bytes = encode(&wrapper, Limits::default()).unwrap();
                assert_eq!(decode(&bytes, Limits::default()).unwrap(), wrapper);
            }
        }
    }
}
