"""Consolidated Markdown, JSON and SARIF governance reports."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from vibeguard.core.report_generator import ensure_vibeguard_dir
from vibeguard.security import Finding, decision_for, risk_score


@dataclass(frozen=True)
class GovernanceReport:
    generated_at: str
    repository: str
    decision: str
    score: int
    files_changed: list[str] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    checks: list[dict[str, Any]] = field(default_factory=list)
    agent: str | None = None
    task: str | None = None


def build_report(root: Path, *, findings: list[Finding], checks: list[dict[str, Any]], files_changed: list[str], agent: str | None = None, task: str | None = None) -> GovernanceReport:
    score = risk_score(findings)
    failed = any(str(item.get("status", "")).lower() == "failed" for item in checks)
    return GovernanceReport(datetime.now(UTC).isoformat(), root.resolve().name, decision_for(score, failed), score, files_changed, findings, checks, agent, task)


def write_report(root: Path, report: GovernanceReport, format_name: str) -> Path:
    directory = ensure_vibeguard_dir(root) / "reports"
    format_name = format_name.lower()
    if format_name in {"md", "markdown"}:
        path = directory / "vibeguard-report.md"
        path.write_text(_markdown(report), encoding="utf-8")
    elif format_name == "json":
        path = directory / "vibeguard-report.json"
        path.write_text(json.dumps(asdict(report), indent=2), encoding="utf-8")
    elif format_name == "sarif":
        path = directory / "vibeguard-report.sarif"
        path.write_text(json.dumps(_sarif(report), indent=2), encoding="utf-8")
    else:
        raise ValueError("Report format must be markdown, json, or sarif.")
    return path


def _markdown(report: GovernanceReport) -> str:
    lines = [
        "# VibeGuard Governance Report",
        "",
        f"- Decision: **{report.decision}**",
        f"- Risk score: **{report.score}/100**",
        f"- Repository: {report.repository}",
        f"- Agent: {report.agent or 'None'}",
        f"- Task: {report.task or 'None'}",
        "",
        "## Files changed",
        *(f"- `{path}`" for path in report.files_changed),
        "",
        "## Verification results",
        *(f"- {item.get('name')}: {item.get('status')} — {str(item.get('details', ''))[:200]}" for item in report.checks),
        "",
        "## Security findings",
        *(f"- **{item.severity}** {item.file}: {item.message} Remediation: {item.remediation}" for item in report.findings),
        "",
        "## Next recommended action",
        "- Resolve blocking checks and high-severity findings, then rerun `vig verify` and `vig report`.",
    ]
    if not report.files_changed:
        lines.insert(lines.index("## Verification results") - 1, "- None")
    if not report.findings:
        lines.insert(lines.index("## Next recommended action") - 1, "- No deterministic findings.")
    return "\n".join(lines) + "\n"


def _sarif(report: GovernanceReport) -> dict[str, Any]:
    levels = {"INFO": "note", "LOW": "note", "MEDIUM": "warning", "HIGH": "error", "CRITICAL": "error"}
    return {
        "version": "2.1.0",
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "runs": [{
            "tool": {"driver": {"name": "VibeGuard", "informationUri": "https://github.com/Sarthak702-droid/VibeGuard"}},
            "results": [{
                "ruleId": finding.category,
                "level": levels[finding.severity],
                "message": {"text": finding.message},
                "locations": [{"physicalLocation": {"artifactLocation": {"uri": finding.file}, "region": {"startLine": finding.line or 1}}}],
            } for finding in report.findings],
        }],
    }
