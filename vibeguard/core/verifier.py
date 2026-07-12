from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
import re
import tomllib

from vibeguard.core.detector import ProjectDetection
from vibeguard.utils.command_runner import run_project_command


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    details: str
    duration: float = 0.0
    command: str = ""
    exit_code: int | None = None


@dataclass(frozen=True)
class VerificationReport:
    status: str
    checks: list[CheckResult] = field(default_factory=list)


def verify_project(root: Path, detection: ProjectDetection, mode: str = "full", timeout: int = 300) -> VerificationReport:
    root = Path(root)
    checks: list[CheckResult] = []
    if "Python" in detection.languages:
        checks.extend(
            [
                _run(root, "python compile", [sys.executable, "-m", "compileall", "."], timeout),
                _run(root, "pytest", [sys.executable, "-m", "pytest"], timeout),
                _run(root, "ruff", [sys.executable, "-m", "ruff", "check", "."], timeout),
            ]
        )
        if mode != "quick":
            checks.extend([_run(root, "bandit", ["bandit", "-r", "."], timeout), _run(root, "pip-audit", ["pip-audit"], timeout)])
            if "mypy" in detection.type_tools:
                checks.append(_run(root, "mypy", [sys.executable, "-m", "mypy", "."], timeout))
            pyproject_text = (root / "pyproject.toml").read_text(encoding="utf-8", errors="ignore").lower() if (root / "pyproject.toml").exists() else ""
            if "black" in pyproject_text:
                checks.append(_run(root, "black format", [sys.executable, "-m", "black", "--check", "."], timeout))
            module = _python_module_name(root)
            if module:
                checks.append(_run(root, "package import", [sys.executable, "-c", f"import {module}"], timeout))
    if "Node.js" in detection.languages:
        if (root / "package.json").exists():
            checks.append(CheckResult("package.json detected", "Passed", "package.json detected"))
        if (root / "tsconfig.json").exists():
            checks.append(CheckResult("TypeScript project detected", "Passed", "tsconfig.json detected"))
        checks.extend(
            [
                _npm_script(root, detection, "test", timeout),
                _npm_script(root, detection, "lint", timeout),
                _npm_script(root, detection, "typecheck", timeout),
            ]
        )
        if mode == "full":
            checks.append(_npm_script(root, detection, "build", timeout))
    if "Go" in detection.languages:
        checks.extend([_run(root, "go test", ["go", "test", "./..."], timeout), _run(root, "go vet", ["go", "vet", "./..."], timeout)])
    if "Java" in detection.languages:
        if detection.package_manager == "maven":
            checks.append(_run(root, "maven test", ["mvn", "test"], timeout))
        else:
            gradle = "./gradlew" if (root / "gradlew").exists() else "gradle"
            checks.append(_run(root, "gradle test", [gradle, "test"], timeout))
    if not checks:
        checks.append(CheckResult("project checks", "Skipped", "No supported Python or Node project detected."))

    if any(check.status == "Failed" for check in checks):
        status = "Failed"
    elif any(check.status in {"Warning", "Skipped"} for check in checks):
        status = "Warning"
    else:
        status = "Passed"
    return VerificationReport(status=status, checks=checks)


def _npm_script(root: Path, detection: ProjectDetection, script: str, timeout: int = 300) -> CheckResult:
    if script not in detection.scripts:
        return CheckResult(script, "Skipped", f"no {script} script found")
    manager = detection.package_manager if detection.package_manager in {"npm", "pnpm", "yarn", "bun"} else "npm"
    if script == "test":
        cmd = [manager, "test"]
    else:
        cmd = [manager, script] if manager == "yarn" else [manager, "run", script]
    return _run(root, script, cmd, timeout)


def _run(root: Path, name: str, command: list[str], timeout: int = 300) -> CheckResult:
    res = run_project_command(root, command, timeout=timeout)
    return CheckResult(name, res.status, res.details, res.duration, res.command_str, res.exit_code)


def _python_module_name(root: Path) -> str | None:
    path = root / "pyproject.toml"
    if not path.exists():
        return None
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return None
    name = str(data.get("project", {}).get("name", "")).replace("-", "_")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        return None
    if (root / name).is_dir() or (root / "src" / name).is_dir():
        return name
    return None
