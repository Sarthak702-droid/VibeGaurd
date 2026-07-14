"""Deterministic secret, dependency and policy analysis."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from vibeguard.config import VibeGuardConfig
from vibeguard.core.diff_analyzer import DiffSummary
from vibeguard.core.risk_engine import SECRET_ASSIGNMENT_PATTERN, SECRET_VALUE_PATTERN


@dataclass(frozen=True)
class Finding:
    category: str
    severity: str
    message: str
    file: str = ""
    line: int | None = None
    remediation: str = "Review and correct before shipping."


def _redacted(line: str) -> str:
    line = SECRET_VALUE_PATTERN.sub("[REDACTED]", line)
    return SECRET_ASSIGNMENT_PATTERN.sub(lambda match: match.group(0).replace(match.group(2), "[REDACTED]"), line)


def scan_secrets(root: Path) -> list[Finding]:
    from vibeguard.core.scanner import scan_project

    findings: list[Finding] = []
    scan = scan_project(root)
    for relative in scan.files:
        path = root / relative
        if relative in scan.large_files:
            continue
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for number, text in enumerate(lines, 1):
            if SECRET_VALUE_PATTERN.search(text) or SECRET_ASSIGNMENT_PATTERN.search(text):
                lowered = text.lower()
                if any(marker in lowered for marker in ("[redacted]", "example", "dummy", "placeholder", "sk_live_demo", "fake_")):
                    continue
                findings.append(
                    Finding(
                        "secret",
                        "CRITICAL",
                        f"Potential credential found: {_redacted(text.strip())[:160]}",
                        relative,
                        number,
                        "Revoke the credential, remove it from history, and load it from a secret store or environment variable.",
                    )
                )
    return findings


MANIFESTS = {"package.json", "requirements.txt", "pyproject.toml", "go.mod", "pom.xml", "build.gradle"}
SUSPICIOUS_NAME = re.compile(r"(?:colourama|reqeusts|crossenv|lodahs|expres$)", re.IGNORECASE)


def scan_dependencies(root: Path, diff: DiffSummary | None = None) -> list[Finding]:
    findings: list[Finding] = []
    changed = {item.path for item in diff.changed_files} if diff else set()
    for name in MANIFESTS:
        path = root / name
        if not path.exists():
            continue
        if changed and name not in changed:
            continue
        if name == "package.json":
            try:
                package = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            for section in ("dependencies", "devDependencies"):
                for dependency in package.get(section, {}):
                    if SUSPICIOUS_NAME.search(dependency):
                        findings.append(Finding("dependency", "HIGH", f"Suspicious package name '{dependency}'.", name, remediation="Confirm the package spelling and publisher."))
        if name in changed:
            findings.append(Finding("dependency", "MEDIUM", "Dependency manifest changed.", name, remediation="Review added packages, versions, lockfile and license impact."))
    if diff:
        removed: dict[str, str] = {}
        added: dict[str, str] = {}
        dependency_line = re.compile(r'^[+-]\s*["\']([A-Za-z0-9@/_.-]+)["\']\s*[:=]\s*["\']([^"\']+)["\']')
        for line in diff.raw_diff.splitlines():
            match = dependency_line.match(line)
            if not match:
                continue
            target = added if line.startswith("+") else removed
            target[match.group(1)] = match.group(2)
        for package, version in added.items():
            if package not in removed:
                findings.append(Finding("dependency", "MEDIUM", f"New dependency '{package}' ({version}) added.", remediation="Verify publisher, maintenance, license, provenance, and necessity."))
            elif _major(version) > _major(removed[package]):
                findings.append(Finding("dependency", "HIGH", f"Major upgrade for '{package}': {removed[package]} → {version}.", remediation="Review breaking changes and run the full regression suite."))
    return findings


def _major(version: str) -> int:
    match = re.search(r"\d+", version)
    return int(match.group()) if match else 0


def policy_findings(diff: DiffSummary, config: VibeGuardConfig) -> list[Finding]:
    findings: list[Finding] = []
    for changed in diff.changed_files:
        normalized = changed.path.replace("\\", "/")
        for protected in config.protected_paths:
            prefix = protected.rstrip("*").rstrip("/")
            if normalized == prefix or normalized.startswith(prefix + "/") or (protected.endswith("*") and normalized.startswith(prefix)):
                findings.append(Finding("policy", "CRITICAL", "Protected path modified.", changed.path, remediation="Obtain explicit review or revert this change."))
                break
        lower = normalized.lower()
        if ".github/workflows" in lower or ".gitlab-ci" in lower:
            findings.append(Finding("ci", "HIGH", "CI/CD configuration changed.", changed.path))
        if "migration" in lower:
            findings.append(Finding("database", "HIGH", "Database migration changed.", changed.path, remediation="Review forward and rollback migration paths."))
        if "auth" in lower or "permission" in lower:
            findings.append(Finding("authentication", "HIGH", "Authentication or authorization code changed.", changed.path))
        if changed.status == "deleted" and any(term in lower for term in ("test", "spec")):
            findings.append(Finding("testing", "HIGH", "Test file deleted.", changed.path))
    paths = [item.path.lower() for item in diff.changed_files]
    if paths and not any(any(term in path for term in ("test", "spec", "__tests__")) for path in paths):
        findings.append(Finding("testing", "MEDIUM", "Production changes have no corresponding test-file change.", remediation="Add or update a regression test, or document why existing coverage is sufficient."))
    total_lines = sum(item.additions + item.deletions for item in diff.changed_files)
    if total_lines > 500:
        findings.append(Finding("change-size", "HIGH", f"Large diff contains {total_lines} changed lines.", remediation="Split unrelated work and review the diff in smaller units."))
    added_lines = "\n".join(line[1:] for line in diff.raw_diff.splitlines() if line.startswith("+") and not line.startswith("+++"))
    if re.search(r"subprocess\.(?:run|Popen)\([^\n]*shell\s*=\s*True", added_lines):
        findings.append(Finding("subprocess", "CRITICAL", "Unsafe subprocess shell execution added.", remediation="Use a validated argument array with shell=False."))
    if re.search(r"(?:verify\s*=\s*False|disable[_-]?security|no[_-]?verify)", added_lines, re.IGNORECASE):
        findings.append(Finding("security-control", "HIGH", "A security verification control may have been disabled.", remediation="Restore verification or obtain explicit security review."))
    return findings


WEIGHTS = {"INFO": 1, "LOW": 5, "MEDIUM": 15, "HIGH": 30, "CRITICAL": 50}


def risk_score(findings: list[Finding]) -> int:
    return min(100, sum(WEIGHTS.get(item.severity, 0) for item in findings))


def decision_for(score: int, has_failed_checks: bool = False) -> str:
    if has_failed_checks or score >= 80:
        return "BLOCKED"
    if score >= 60:
        return "REVIEW_REQUIRED"
    if score >= 30:
        return "PASS_WITH_WARNINGS"
    return "PASS"


def serialize_findings(findings: list[Finding]) -> list[dict[str, object]]:
    return [asdict(item) for item in findings]
