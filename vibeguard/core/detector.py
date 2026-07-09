from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class ProjectDetection:
    primary_type: str
    languages: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    package_manager: str | None = None
    scripts: dict[str, str] = field(default_factory=dict)


def _read_package_json(root: Path) -> dict:
    package_file = root / "package.json"
    if not package_file.exists():
        return {}
    try:
        return json.loads(package_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _deps(package: dict) -> dict[str, str]:
    merged: dict[str, str] = {}
    for key in ("dependencies", "devDependencies", "peerDependencies"):
        value = package.get(key)
        if isinstance(value, dict):
            merged.update(value)
    return merged


def detect_project(root: Path) -> ProjectDetection:
    root = Path(root)
    package = _read_package_json(root)
    deps = _deps(package)
    languages: list[str] = []
    frameworks: list[str] = []
    package_manager: str | None = None

    if package:
        languages.append("Node.js")
        if (root / "pnpm-lock.yaml").exists():
            package_manager = "pnpm"
        elif (root / "yarn.lock").exists():
            package_manager = "yarn"
        else:
            package_manager = "npm"

    if (root / "pyproject.toml").exists() or (root / "requirements.txt").exists() or any(root.glob("*.py")):
        languages.append("Python")

    if "next" in deps:
        frameworks.append("Next.js")
    if "react" in deps:
        frameworks.append("React")
    if "react-native" in deps:
        frameworks.append("React Native")
    if "expo" in deps or (root / "app.json").exists():
        frameworks.append("Expo")
    if (root / "tsconfig.json").exists() or "typescript" in deps:
        frameworks.append("TypeScript")

    req_text = ""
    if (root / "requirements.txt").exists():
        req_text = (root / "requirements.txt").read_text(encoding="utf-8", errors="ignore").lower()
    if "fastapi" in req_text:
        frameworks.append("FastAPI")
    if "flask" in req_text:
        frameworks.append("Flask")
    if (root / "manage.py").exists() or "django" in req_text:
        frameworks.append("Django")

    if "Expo" in frameworks and "React Native" in frameworks:
        primary = "React Native / Expo"
    elif "Next.js" in frameworks:
        primary = "Next.js"
    elif "React" in frameworks:
        primary = "React"
    elif "Python" in languages:
        primary = "Python"
    elif "Node.js" in languages:
        primary = "Node.js"
    else:
        primary = "Unknown"

    return ProjectDetection(
        primary_type=primary,
        languages=_unique(languages),
        frameworks=_unique(frameworks),
        package_manager=package_manager,
        scripts=package.get("scripts", {}) if isinstance(package.get("scripts"), dict) else {},
    )


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result

