//! Provider-neutral prompt rendering.

use vibeguard_core::ScanResult;
pub fn build(scan: &ScanResult, goal: &str, files: &[String], agent: &str) -> String {
    let paths = files
        .iter()
        .map(|path| format!("- `{path}`"))
        .collect::<Vec<_>>()
        .join("\n");
    let prefix = match agent {
        "codex" => "<!-- Target agent: Codex CLI -->\n",
        "claude" => "<!-- Target agent: Claude Code -->\n",
        "gemini" => "<!-- Target agent: Gemini CLI -->\n",
        "aider" => "<!-- Target agent: Aider -->\n",
        _ => "",
    };
    format!(
        "{prefix}# AI Coding Task\n\n## Goal\n{goal}\n\n## Repository\n- Type: {}\n- Frameworks: {}\n\n## Files to Inspect\n{}\n\n## Guardrails\n- Do not rewrite the project or change unrelated files.\n- Do not read or expose environment files, credentials, or private keys.\n- Add tests for changed behavior.\n- Run relevant tests, linting, and type checks.\n\n## Acceptance Criteria\n- Implement only the stated goal.\n- Explain each changed file and any remaining limitation.\n",
        scan.detection.primary_type,
        scan.detection.frameworks.join(", "),
        if paths.is_empty() {
            "- Inspect the detected manifests first."
        } else {
            &paths
        }
    )
}
