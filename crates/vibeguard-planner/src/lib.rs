//! Offline template-driven implementation planning.

use vibeguard_core::ScanResult;
pub fn build(scan: &ScanResult, goal: &str) -> String {
    let files = scan
        .important_files
        .iter()
        .take(12)
        .map(|file| format!("- `{file}`"))
        .collect::<Vec<_>>()
        .join("\n");
    let risk = if [
        "auth",
        "login",
        "otp",
        "payment",
        "permission",
        "migration",
        "security",
    ]
    .iter()
    .any(|term| goal.to_ascii_lowercase().contains(term))
    {
        "High"
    } else {
        "Medium"
    };
    format!(
        "# Implementation Plan\n\n## Goal\n{goal}\n\n## Current Architecture\n- {}\n- Languages: {}\n\n## Assumptions\n- Preserve public interfaces and existing conventions.\n- Make the smallest reviewable change.\n\n## Likely Affected Files\n{}\n\n## Tasks\n1. Inspect affected interfaces and tests.\n2. Implement the scoped success and failure paths.\n3. Add or update regression tests.\n4. Run verification and review the diff.\n\n## Risks\n- Estimated risk: {risk}\n- Do not alter credentials, CI, migrations, or protected files without review.\n\n## Acceptance Criteria\n- The goal works end to end.\n- Tests cover changed behavior.\n- No secrets or unrelated changes are introduced.\n\n## Rollback\n- Revert only files attributable to this task and rerun verification.\n",
        scan.detection.primary_type,
        scan.detection.languages.join(", "),
        if files.is_empty() {
            "- Inspect manifests and entry points"
        } else {
            &files
        }
    )
}
