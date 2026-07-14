//! Rule-based diff risk analysis with documented additive scoring.

use regex::Regex;
use vibeguard_core::{Finding, Severity};
use vibeguard_git::DiffSummary;
pub fn analyze(diff: &DiffSummary) -> Vec<Finding> {
    let mut findings = Vec::new();
    for file in &diff.files {
        let path = file.path.to_ascii_lowercase();
        if path.contains("auth") || path.contains("permission") {
            findings.push(finding(
                "VG-RISK-001",
                "Authentication or authorization changed",
                Severity::High,
                "authentication",
                &file.path,
                "Authentication and authorization changes require manual review.",
            ));
        }
        if path.contains("migration") {
            findings.push(finding(
                "VG-RISK-002",
                "Database migration changed",
                Severity::High,
                "database",
                &file.path,
                "Review forward and rollback migration paths.",
            ));
        }
        if path.contains(".github/workflows") || path.contains(".gitlab-ci") {
            findings.push(finding(
                "VG-RISK-003",
                "CI/CD configuration changed",
                Severity::High,
                "ci_cd",
                &file.path,
                "Review workflow permissions and supplied credentials.",
            ));
        }
        if file.status == "deleted" && (path.contains("test") || path.contains("spec")) {
            findings.push(finding(
                "VG-RISK-004",
                "Test file deleted",
                Severity::High,
                "testing",
                &file.path,
                "Preserve coverage or document a replacement.",
            ));
        }
    }
    if !diff.files.is_empty()
        && !diff
            .files
            .iter()
            .any(|file| file.path.contains("test") || file.path.contains("spec"))
    {
        findings.push(finding(
            "VG-RISK-005",
            "Production changes without test changes",
            Severity::Medium,
            "testing",
            "",
            "Add a regression test or document existing coverage.",
        ));
    }
    if diff
        .files
        .iter()
        .map(|file| file.additions + file.deletions)
        .sum::<u64>()
        > 500
    {
        findings.push(finding(
            "VG-RISK-006",
            "Large diff",
            Severity::High,
            "change_size",
            "",
            "Split unrelated changes into reviewable commits.",
        ));
    }
    if Regex::new(r"(?i)(shell\s*=\s*true|verify\s*=\s*false|disable[_-]?security)")
        .is_ok_and(|pattern| pattern.is_match(&diff.raw))
    {
        findings.push(finding(
            "VG-RISK-007",
            "Security control may be disabled",
            Severity::Critical,
            "security_control",
            "",
            "Restore the control or obtain explicit security approval.",
        ));
    }
    findings
}
pub fn score(findings: &[Finding]) -> u8 {
    findings
        .iter()
        .fold(0u8, |total, finding| {
            total.saturating_add(finding.severity.score())
        })
        .min(100)
}
fn finding(
    rule: &str,
    title: &str,
    severity: Severity,
    category: &str,
    file: &str,
    action: &str,
) -> Finding {
    Finding {
        rule_id: rule.to_owned(),
        title: title.to_owned(),
        description: title.to_owned(),
        severity,
        category: category.to_owned(),
        file: file.to_owned(),
        line: None,
        evidence: "Path and diff metadata".to_owned(),
        recommended_action: action.to_owned(),
        confidence: "high".to_owned(),
        suppressible: true,
    }
}

#[cfg(test)]
mod tests {
    use super::{analyze, score};
    use vibeguard_git::{DiffFile, DiffSummary};

    #[test]
    fn auth_change_is_high_risk() {
        let report = DiffSummary {
            files: vec![DiffFile {
                path: "src/auth/login.rs".to_owned(),
                status: "modified".to_owned(),
                additions: 1,
                deletions: 0,
            }],
            raw: String::new(),
            available: true,
        };
        let findings = analyze(&report);
        assert!(score(&findings) >= 30);
    }
}
