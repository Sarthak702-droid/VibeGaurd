from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

from vibeguard.core.detector import ProjectDetection
from vibeguard.utils.command_runner import run_project_command


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    details: str


@dataclass(frozen=True)
class VerificationReport:
    status: str
    checks: list[CheckResult] = field(default_factory=list)


def verify_project(root: Path, detection: ProjectDetection) -> VerificationReport:
    root = Path(root)
    checks: list[CheckResult] = []
    if "Python" in detection.languages:
        checks.extend(
            [
                _run(root, "python compile", [sys.executable, "-m", "compileall", "."]),
                _run(root, "pytest", ["pytest"]),
                _run(root, "ruff", ["ruff", "check", "."]),
                _run(root, "bandit", ["bandit", "-r", "."]),
                _run(root, "pip-audit", ["pip-audit"]),
            ]
        )
    if "Node.js" in detection.languages:
        if (root / "package.json").exists():
            checks.append(CheckResult("package.json detected", "Passed", "package.json detected"))
        if (root / "tsconfig.json").exists():
            checks.append(CheckResult("TypeScript project detected", "Passed", "tsconfig.json detected"))
        checks.extend(
            [
                _npm_script(root, detection, "test"),
                _npm_script(root, detection, "lint"),
                _npm_script(root, detection, "typecheck"),
            ]
        )
    if not checks:
        checks.append(CheckResult("project checks", "Skipped", "No supported Python or Node project detected."))

    if any(check.status == "Failed" for check in checks):
        status = "Failed"
    elif any(check.status in {"Warning", "Skipped"} for check in checks):
        status = "Warning"
    else:
        status = "Passed"
    return VerificationReport(status=status, checks=checks)


def _npm_script(root: Path, detection: ProjectDetection, script: str) -> CheckResult:
    if script not in detection.scripts:
        return CheckResult(script, "Skipped", f"no {script} script found")
    if script == "test":
        cmd = ["npm", "test"]
    else:
        cmd = ["npm", "run", script]
    return _run(root, script, cmd)


def _run(root: Path, name: str, command: list[str]) -> CheckResult:
    res = run_project_command(root, command)
    return CheckResult(name, res.status, res.details)
