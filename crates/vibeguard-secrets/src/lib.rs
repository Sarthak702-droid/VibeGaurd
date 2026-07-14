//! Offline secret detection with redacted evidence only.

use regex::Regex;
use std::{fs, path::Path};
use vibeguard_core::{Finding, Severity, redact};
pub fn scan(root: &Path, files: &[String], suppressions: &[String]) -> Vec<Finding> {
    let patterns = [
        "ghp_[A-Za-z0-9]{20,}",
        "github_pat_[A-Za-z0-9_]{20,}",
        "AKIA[0-9A-Z]{16}",
        "(?i)(api[_-]?key|secret|token|password)\\s*[:=]\\s*['\\\"]?[^\\s'\\\"]{8,}",
        "-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    ];
    let compiled = patterns
        .iter()
        .filter_map(|pattern| Regex::new(pattern).ok())
        .collect::<Vec<_>>();
    let mut findings = Vec::new();
    for file in files {
        let content = fs::read_to_string(root.join(file)).unwrap_or_default();
        for (index, line) in content.lines().enumerate() {
            if suppressions.iter().any(|item| line.contains(item))
                || line.to_ascii_lowercase().contains("example")
                || line.to_ascii_lowercase().contains("placeholder")
            {
                continue;
            }
            if compiled.iter().any(|pattern| pattern.is_match(line)) {
                findings.push(Finding { rule_id: "VG-SECRET-001".to_owned(), title: "Potential secret detected".to_owned(), description: "A credential-like value was found in repository text.".to_owned(), severity: Severity::Critical, category: "secrets".to_owned(), file: file.clone(), line: Some((index + 1) as u32), evidence: redact(line).chars().take(160).collect(), recommended_action: "Revoke the value, remove it from version control, and load it from a secret manager or environment.".to_owned(), confidence: "medium".to_owned(), suppressible: true });
            }
        }
    }
    findings
}
