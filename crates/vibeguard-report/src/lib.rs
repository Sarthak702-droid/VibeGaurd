//! Versioned terminal, JSON, Markdown, and SARIF report rendering.

use std::{
    fs,
    path::{Path, PathBuf},
};
use vibeguard_core::{
    CheckResult, Finding, REPORT_SCHEMA_VERSION, ScanResult, Severity, VibeGuardError,
};
#[derive(Clone, Copy, Debug)]
pub enum Format {
    Terminal,
    Json,
    Markdown,
    Sarif,
}
impl Format {
    pub fn parse(value: &str) -> Result<Self, VibeGuardError> {
        match value {
            "terminal" => Ok(Self::Terminal),
            "json" => Ok(Self::Json),
            "markdown" | "md" => Ok(Self::Markdown),
            "sarif" => Ok(Self::Sarif),
            _ => Err(VibeGuardError::InvalidInput(format!(
                "unsupported format '{value}'; use terminal, json, markdown, or sarif"
            ))),
        }
    }
    pub fn extension(self) -> &'static str {
        match self {
            Self::Terminal | Self::Markdown => "md",
            Self::Json => "json",
            Self::Sarif => "sarif",
        }
    }
}
pub fn markdown(scan: &ScanResult, findings: &[Finding], checks: &[CheckResult]) -> String {
    let risk = findings
        .iter()
        .fold(0u8, |total, finding| {
            total.saturating_add(finding.severity.score())
        })
        .min(100);
    let mut output = format!(
        "# VibeGuard Report\n\nSchema version: {REPORT_SCHEMA_VERSION}\n\n## Repository\n- {}\n- Commit: {}\n\n## Scan\n- Files scanned: {} / {} tracked\n- Skipped binaries: {}\n- Skipped oversized: {}\n- Skipped generated: {}\n- Skipped sensitive: {}\n\n## Technologies\n- Type: {}\n- Languages: {}\n- Frameworks: {}\n\n## Risk\n- Score: {risk}/100\n",
        scan.repository,
        scan.commit.as_deref().unwrap_or("working tree"),
        scan.statistics.scanned,
        scan.statistics.tracked,
        scan.statistics.skipped_binary,
        scan.statistics.skipped_oversized,
        scan.statistics.skipped_generated,
        scan.statistics.skipped_sensitive,
        scan.detection.primary_type,
        scan.detection.languages.join(", "),
        scan.detection.frameworks.join(", ")
    );
    output.push_str("\n## Findings\n");
    if findings.is_empty() {
        output.push_str("- None\n");
    }
    for finding in findings {
        output.push_str(&format!(
            "- {:?} `{}` {}{}\n",
            finding.severity,
            finding.rule_id,
            finding.title,
            if finding.file.is_empty() {
                String::new()
            } else {
                format!(" ({})", finding.file)
            }
        ));
    }
    output.push_str("\n## Verification\n");
    if checks.is_empty() {
        output.push_str("- Not requested\n");
    }
    for check in checks {
        output.push_str(&format!("- {:?}: {}\n", check.status, check.name));
    }
    output
}
pub fn json(
    scan: &ScanResult,
    findings: &[Finding],
    checks: &[CheckResult],
) -> Result<String, VibeGuardError> {
    serde_json::to_string_pretty(&serde_json::json!({"schema_version": REPORT_SCHEMA_VERSION, "vibeguard_version": env!("CARGO_PKG_VERSION"), "scan": scan, "findings": findings, "verification": checks})).map_err(|error| VibeGuardError::Internal(error.to_string()))
}
pub fn sarif(findings: &[Finding]) -> Result<String, VibeGuardError> {
    let results: Vec<_> = findings.iter().map(|finding| serde_json::json!({"ruleId": finding.rule_id, "level": match finding.severity { Severity::Critical | Severity::High => "error", Severity::Medium => "warning", _ => "note" }, "message": {"text": finding.title}, "locations": [{"physicalLocation": {"artifactLocation": {"uri": finding.file}, "region": {"startLine": finding.line.unwrap_or(1)}}}]})).collect();
    serde_json::to_string_pretty(&serde_json::json!({"version":"2.1.0", "$schema":"https://json.schemastore.org/sarif-2.1.0.json", "runs":[{"tool":{"driver":{"name":"VibeGuard","version":env!("CARGO_PKG_VERSION")}},"results":results}]})).map_err(|error| VibeGuardError::Internal(error.to_string()))
}
pub fn write(
    root: &Path,
    format: Format,
    content: &str,
    output: Option<&Path>,
) -> Result<PathBuf, VibeGuardError> {
    let path = output.map(PathBuf::from).unwrap_or_else(|| {
        root.join(".vibeguard")
            .join("reports")
            .join(format!("vibeguard-report.{}", format.extension()))
    });
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|error| VibeGuardError::Io(error.to_string()))?;
    }
    fs::write(&path, content).map_err(|error| VibeGuardError::Io(error.to_string()))?;
    Ok(path)
}
