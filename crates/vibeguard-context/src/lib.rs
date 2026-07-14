//! Deterministic context-file ranking and bounded pack creation.

use regex::Regex;
use std::{fs, path::Path};
use vibeguard_core::{ScanResult, VibeGuardError};

#[derive(Clone, Debug)]
pub struct PackedFile {
    pub path: String,
    pub reason: String,
    pub estimated_tokens: usize,
}
#[derive(Clone, Debug)]
pub struct ContextPack {
    pub included: Vec<PackedFile>,
    pub excluded: Vec<String>,
    pub estimated_tokens: usize,
    pub markdown: String,
}
pub fn build(
    root: &Path,
    scan: &ScanResult,
    goal: &str,
    budget: usize,
) -> Result<ContextPack, VibeGuardError> {
    if goal.trim().is_empty() || budget == 0 {
        return Err(VibeGuardError::InvalidInput(
            "goal and token budget are required".to_owned(),
        ));
    }
    let words = Regex::new(r"[A-Za-z][A-Za-z0-9_-]+$")
        .map_err(|error| VibeGuardError::Internal(error.to_string()))?;
    let terms: Vec<String> = goal
        .split_whitespace()
        .filter_map(|item| {
            words
                .find(item)
                .map(|item| item.as_str().to_ascii_lowercase())
        })
        .collect();
    let mut candidates = Vec::new();
    for path in &scan.files {
        let content = fs::read_to_string(root.join(path)).unwrap_or_default();
        let lower = format!(
            "{} {}",
            path.to_ascii_lowercase(),
            content.to_ascii_lowercase()
        );
        let score = terms
            .iter()
            .map(|term| {
                if path.to_ascii_lowercase().contains(term) {
                    5
                } else if lower.contains(term) {
                    3
                } else {
                    0
                }
            })
            .sum::<i32>()
            + if scan.important_files.contains(path) {
                4
            } else {
                0
            };
        candidates.push((score, path.clone(), content));
    }
    candidates.sort_by(|left, right| right.0.cmp(&left.0).then_with(|| left.1.cmp(&right.1)));
    let mut included = Vec::new();
    let mut excluded = Vec::new();
    let mut total = 0;
    for (score, path, content) in candidates {
        let tokens = content.len().div_ceil(4).max(1);
        if score < 3 || total + tokens > budget {
            excluded.push(path);
        } else {
            let reason = if scan.important_files.contains(&path) {
                "Project configuration or dependency manifest"
            } else {
                "Task relevance"
            };
            total += tokens;
            included.push(PackedFile {
                path,
                reason: reason.to_owned(),
                estimated_tokens: tokens,
            });
        }
    }
    let selection = included
        .iter()
        .map(|file| format!("- `{}` — {}", file.path, file.reason))
        .collect::<Vec<_>>()
        .join("\n");
    let markdown = format!(
        "# VibeGuard Context Pack\n\n## Goal\n{goal}\n\n## Project Type\n{}\n\n## Selected Files and Reasons\n{}\n\n## Estimated Tokens\n{total} / {budget}\n\n## Safety\n- Sensitive, binary, generated, and oversized files are excluded.\n- VibeGuard does not send this data to an external provider.\n",
        scan.detection.primary_type,
        if selection.is_empty() {
            "- None"
        } else {
            &selection
        }
    );
    Ok(ContextPack {
        included,
        excluded,
        estimated_tokens: total,
        markdown,
    })
}
