from __future__ import annotations

import sys
from pathlib import Path

from vibeguard.core.diff_analyzer import DiffSummary
from vibeguard.core.risk_engine import Risk, RiskReport
from vibeguard.core.verifier import VerificationReport
from vibeguard.utils.os_utils import get_os_name


TEST_TERMS = (".test.", ".spec.", "__tests__", "/tests/", "\\tests\\")


def ensure_vibeguard_dir(root: Path) -> Path:
    out = Path(root) / ".vibeguard"
    (out / "reports").mkdir(parents=True, exist_ok=True)
    (out / "cache").mkdir(parents=True, exist_ok=True)
    return out


def write_text(root: Path, relative: str, content: str) -> Path:
    out = ensure_vibeguard_dir(root)
    path = out / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def render_diff_report(diff: DiffSummary) -> str:
    changed_paths = [changed.path for changed in diff.changed_files]
    risk_notes = _diff_risk_notes(changed_paths)
    lines = ["# VibeGuard Diff Report", "", "## Changed Files"]
    if not changed_paths:
        lines.append("No uncommitted Git diff detected.")
    else:
        lines.extend(f"- {path}" for path in changed_paths)
    lines.extend(["", "## Git Diff Summary"])
    if not changed_paths:
        lines.append("- No changed files found.")
    else:
        lines.extend(f"- {changed.path} changed" for changed in diff.changed_files)
    lines.extend(["", "## Detected Risk Notes"])
    if risk_notes:
        lines.extend(f"- {note}" for note in risk_notes)
    else:
        lines.append("- No obvious diff-level risk notes detected.")
    lines.extend(
        [
            "",
            "## Suggested Review Focus",
            "- Changed behavior and public interfaces",
            "- Validation and error handling",
            "- Authentication, authorization, and data boundaries",
            "- Dependency, configuration, CI, and migration impact",
            "- Test coverage and rollback path",
            "- Secret leakage",
        ]
    )
    return "\n".join(lines) + "\n"


def render_risk_report(report: RiskReport) -> str:
    os_name = get_os_name().title()
    python_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    grouped: dict[str, list[Risk]] = {"HIGH": [], "MEDIUM": [], "LOW": [], "INFO": []}
    for risk in report.risks:
        grouped.setdefault(risk.severity, []).append(risk)
    lines = [
        "# VibeGuard Risk Report",
        "",
        "## System Info",
        f"- Operating System: {os_name}",
        f"- Python Version: {python_ver}",
        "",
        "## Overall Risk Level",
        report.overall.title(),
        "",
        "## Risks Found"
    ]
    if not report.risks:
        lines.append("No obvious risky patterns detected.")
    for severity in ("HIGH", "MEDIUM", "LOW", "INFO"):
        if not grouped.get(severity):
            continue
        lines.extend(["", f"### {severity}"])
        for risk in grouped[severity]:
            lines.append(f"{severity} {risk.message}")
            if risk.path:
                lines.append(f"File: {risk.path}")
            lines.append(f"Reason: {_risk_reason(risk)}")
            lines.append("")
    lines.extend(
        [
            "## Recommended Actions",
            "- Review high-risk and protected-path changes manually.",
            "- Add regression tests for changed behavior.",
            "- Check for hardcoded API keys.",
            "- Run VibeGuard verify.",
        ]
    )
    return "\n".join(lines).replace("\n\n## Recommended", "\n## Recommended") + "\n"


def render_verification_report(report: VerificationReport, project_type: str = "Unknown", package_manager: str = "Unknown") -> str:
    os_name = get_os_name().title()
    python_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    passed = sum(1 for c in report.checks if c.status == "Passed")
    failed = sum(1 for c in report.checks if c.status == "Failed")
    skipped = sum(1 for c in report.checks if c.status == "Skipped")
    
    commands_run = sum(1 for c in report.checks if c.status in ("Passed", "Failed") and c.name not in ("package.json detected", "TypeScript project detected"))
    commands_skipped = sum(1 for c in report.checks if c.status == "Skipped" and c.name not in ("package.json detected", "TypeScript project detected"))

    lines = [
        "# VibeGuard Verification Report",
        "",
        "## System Info",
        f"- Operating System: {os_name}",
        f"- Python Version: {python_ver}",
        f"- Project Type: {project_type}",
        f"- Package Manager: {package_manager}",
        "",
        "## Summary",
        f"- Status: **{report.status}**",
        f"- Checks Passed: {passed}",
        f"- Checks Failed: {failed}",
        f"- Checks Skipped: {skipped}",
        f"- Commands Run: {commands_run}",
        f"- Commands Skipped: {commands_skipped}",
        "",
        "## Check Details",
        "| Check | Status | Details |",
        "|---|---|---|",
    ]
    for check in report.checks:
        details = check.details.replace("\n", " ")[:240]
        lines.append(f"| {check.name} | {check.status} | {details} |")
    return "\n".join(lines) + "\n"


def _diff_risk_notes(paths: list[str]) -> list[str]:
    notes: list[str] = []
    lower_paths = [path.lower() for path in paths]
    if any("auth" in path for path in lower_paths):
        notes.append("Auth-related file changed.")
    if paths and not any(any(term in path for term in TEST_TERMS) for path in lower_paths):
        notes.append("No test file changed.")
    if notes:
        notes.append("Review validation and error handling carefully.")
    return notes


def _risk_reason(risk) -> str:
    message = risk.message.lower()
    if "auth" in message:
        return "auth-related files require manual review"
    if "no test" in message:
        return "feature code changed without test update"
    if "secret" in message:
        return "changed code contains possible hardcoded secret/API key/token"
    if "dependency" in message or "lockfile" in message:
        return "dependency changes can affect runtime and supply-chain safety"
    if "deleted" in message:
        return "deleted files may break imports or behavior"
    if "large" in message:
        return "large diffs are harder to review and may include unrelated edits"
    return risk.message.rstrip(".")
