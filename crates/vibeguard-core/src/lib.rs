//! Stable domain types shared by VibeGuard crates.

use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use thiserror::Error;

pub const REPORT_SCHEMA_VERSION: &str = "1.0";

#[derive(Clone, Copy, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "lowercase")]
pub enum Severity {
    Info,
    Low,
    Medium,
    High,
    Critical,
}

impl Severity {
    pub const fn score(self) -> u8 {
        match self {
            Self::Info => 1,
            Self::Low => 5,
            Self::Medium => 15,
            Self::High => 30,
            Self::Critical => 50,
        }
    }

    pub fn parse(value: &str) -> Option<Self> {
        match value.to_ascii_lowercase().as_str() {
            "info" => Some(Self::Info),
            "low" => Some(Self::Low),
            "medium" => Some(Self::Medium),
            "high" => Some(Self::High),
            "critical" => Some(Self::Critical),
            _ => None,
        }
    }
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct Finding {
    pub rule_id: String,
    pub title: String,
    pub description: String,
    pub severity: Severity,
    pub category: String,
    pub file: String,
    pub line: Option<u32>,
    pub evidence: String,
    pub recommended_action: String,
    pub confidence: String,
    pub suppressible: bool,
}

#[derive(Clone, Debug, Default, Deserialize, Serialize)]
pub struct FileStatistics {
    pub tracked: u64,
    pub scanned: u64,
    pub skipped_binary: u64,
    pub skipped_oversized: u64,
    pub skipped_generated: u64,
    pub skipped_sensitive: u64,
    pub unreadable: u64,
}

#[derive(Clone, Debug, Default, Deserialize, Serialize)]
pub struct Detection {
    pub primary_type: String,
    pub languages: Vec<String>,
    pub frameworks: Vec<String>,
    pub package_manager: Option<String>,
    pub manifests: Vec<String>,
    pub entry_points: Vec<String>,
    pub source_dirs: Vec<String>,
    pub test_dirs: Vec<String>,
    pub test_tools: Vec<String>,
    pub lint_tools: Vec<String>,
    pub type_tools: Vec<String>,
}

#[derive(Clone, Debug, Default, Deserialize, Serialize)]
pub struct ScanResult {
    pub root: PathBuf,
    pub repository: String,
    pub commit: Option<String>,
    pub detection: Detection,
    pub files: Vec<String>,
    pub important_files: Vec<String>,
    pub statistics: FileStatistics,
    pub warnings: Vec<String>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct CheckResult {
    pub name: String,
    pub status: CheckStatus,
    pub details: String,
    pub command: Vec<String>,
    pub exit_code: Option<i32>,
    pub duration_ms: u128,
}

#[derive(Clone, Copy, Debug, Deserialize, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum CheckStatus {
    Passed,
    Failed,
    Skipped,
    TimedOut,
}

#[derive(Clone, Debug, Error)]
pub enum VibeGuardError {
    #[error("invalid input: {0}")]
    InvalidInput(String),
    #[error("configuration error: {0}")]
    Configuration(String),
    #[error("authentication required for {0}")]
    AuthenticationRequired(String),
    #[error("permission denied for {0}")]
    PermissionDenied(String),
    #[error("git/network failure: {0}")]
    Git(String),
    #[error("unsupported environment: {0}")]
    Unsupported(String),
    #[error("I/O error: {0}")]
    Io(String),
    #[error("internal VibeGuard error: {0}")]
    Internal(String),
}

impl VibeGuardError {
    pub const fn exit_code(&self) -> i32 {
        match self {
            Self::InvalidInput(_) | Self::Configuration(_) => 2,
            Self::AuthenticationRequired(_) | Self::PermissionDenied(_) => 3,
            Self::Git(_) => 4,
            Self::Unsupported(_) => 6,
            Self::Io(_) | Self::Internal(_) => 7,
        }
    }
}

pub fn redact(value: &str) -> String {
    let mut output = value.to_owned();
    for marker in ["ghp_", "github_pat_", "sk-", "xoxb-", "AIza"] {
        let mut start = 0;
        while let Some(offset) = output[start..].find(marker) {
            let begin = start + offset;
            let end = output[begin..]
                .find(|c: char| c.is_whitespace() || matches!(c, '\'' | '\"' | '&'))
                .map(|index| begin + index)
                .unwrap_or(output.len());
            let secret = &output[begin..end];
            let replacement = if secret.len() > 8 {
                format!("{}...{}", &secret[..4], &secret[secret.len() - 4..])
            } else {
                "[REDACTED]".to_owned()
            };
            output.replace_range(begin..end, &replacement);
            start = begin + replacement.len();
        }
    }
    output
}

#[cfg(test)]
mod tests {
    use super::{Severity, VibeGuardError, redact};

    #[test]
    fn redacts_token_prefixes() {
        let rendered = redact("authorization ghp_abcdefghijklmnopqrstuvwxyz123456");
        assert!(!rendered.contains("abcdefghijklmnopqrstuvwxyz"));
        assert!(rendered.contains("ghp_...3456"));
    }

    #[test]
    fn maps_stable_exit_codes() {
        assert_eq!(
            VibeGuardError::Configuration("bad".to_owned()).exit_code(),
            2
        );
        assert_eq!(
            VibeGuardError::AuthenticationRequired("repo".to_owned()).exit_code(),
            3
        );
        assert_eq!(Severity::Critical.score(), 50);
    }
}
