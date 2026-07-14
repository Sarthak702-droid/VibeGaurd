from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from vibeguard.core.diff_analyzer import DiffSummary


SECRET_NAME_PATTERN = r"(?:api[_-]?key|apikey|secret|client[_-]?secret|access[_-]?token|refresh[_-]?token|auth[_-]?token|bearer|password|private[_-]?key)"
SECRET_ASSIGNMENT_PATTERN = re.compile(
    rf"\b{SECRET_NAME_PATTERN}\b\s*[:=]\s*([\"'])([^\"']{{8,}})\1",
    re.IGNORECASE,
)
SECRET_VALUE_PATTERN = re.compile(
    r"(BEGIN RSA PRIVATE KEY|BEGIN OPENSSH PRIVATE KEY|sk-[A-Za-z0-9_-]{8,}|sk_live_[A-Za-z0-9_-]{8,}|ghp_[A-Za-z0-9_]{8,}|github_pat_[A-Za-z0-9_]{8,}|xoxb-[A-Za-z0-9-]{8,}|AIza[A-Za-z0-9_-]{8,})",
    re.IGNORECASE,
)
HIGH_PATH_TERMS = ("auth", "payment", "billing", "permission", "security", "middleware", "admin", "migration")
# We also include 'route', 'api', 'schema', 'model', 'navigation', 'config' as low/medium path terms
MEDIUM_PATH_TERMS = ("route", "api", "schema", "model", "navigation", "config")
TEST_TERMS = (".test.", ".spec.", "__tests__", "/tests/", "\\tests\\")


@dataclass(frozen=True)
class Risk:
    severity: str
    path: str
    message: str


@dataclass(frozen=True)
class RiskReport:
    overall: str
    risks: list[Risk] = field(default_factory=list)


def analyze_risks(diff: DiffSummary) -> RiskReport:
    risks: list[Risk] = []
    paths = [changed.path for changed in diff.changed_files]
    has_tests = any(any(term in path.lower() for term in TEST_TERMS) for path in paths)

    for changed in diff.changed_files:
        lower = changed.path.lower()
        if Path(changed.path).name.startswith(".env"):
            risks.append(Risk("HIGH", changed.path, "Environment file changed"))
        if any(term in lower for term in HIGH_PATH_TERMS):
            label = "Auth" if "auth" in lower else "High-risk"
            risks.append(Risk("MEDIUM", changed.path, f"{label} logic changed"))
        elif any(term in lower for term in MEDIUM_PATH_TERMS):
            risks.append(Risk("LOW", changed.path, "Sensitive app structure changed"))
        if changed.status == "deleted":
            risks.append(Risk("HIGH", changed.path, "File deleted"))
        if changed.additions + changed.deletions > 250:
            risks.append(Risk("MEDIUM", changed.path, "Large change size"))
        if Path(changed.path).name in {"package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml"}:
            risks.append(Risk("MEDIUM", changed.path, "Dependency or lockfile changed"))

    found_secrets = _find_secrets_in_diff(diff.raw_diff)
    for path, redacted_line in found_secrets:
        risks.append(Risk("HIGH", path, f"Secret-like string found. Redacted line: {redacted_line}"))

    if paths and not has_tests:
        risks.append(Risk("MEDIUM", "", "No test file changed"))

    overall = "INFO"
    if any(r.severity == "HIGH" for r in risks):
        overall = "HIGH"
    elif any(r.severity == "MEDIUM" for r in risks):
        overall = "MEDIUM"
    elif any(r.severity == "LOW" for r in risks):
        overall = "LOW"
    return RiskReport(overall=overall, risks=risks)


def _redact_secrets_in_line(line: str) -> str:
    def repl(match):
        full = match.group(0)
        quote = match.group(1)
        val = match.group(2)
        if val == "[REDACTED]":
            return full
        return full.replace(quote + val + quote, quote + "[REDACTED]" + quote)

    redacted = SECRET_ASSIGNMENT_PATTERN.sub(repl, line)
    redacted = SECRET_VALUE_PATTERN.sub("[REDACTED]", redacted)
    return redacted


def _find_secrets_in_diff(raw_diff: str) -> list[tuple[str, str]]:
    current_file = ""
    found: list[tuple[str, str]] = []
    for line in raw_diff.splitlines():
        if line.startswith("diff --git a/"):
            parts = line.split(" ")
            if len(parts) >= 3:
                current_file = parts[2]
                if current_file.startswith("a/"):
                    current_file = current_file[2:]
        elif line.startswith("+++ b/"):
            current_file = line[6:]
        elif line.startswith("+") and not line.startswith("+++"):
            added = line[1:].strip()
            if SECRET_VALUE_PATTERN.search(added) or SECRET_ASSIGNMENT_PATTERN.search(added):
                redacted = _redact_secrets_in_line(added)
                found.append((current_file, redacted))
    return found
