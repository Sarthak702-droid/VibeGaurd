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
    entry_points: list[str] = field(default_factory=list)
    source_dirs: list[str] = field(default_factory=list)
    test_dirs: list[str] = field(default_factory=list)
    manifests: list[str] = field(default_factory=list)
    test_tools: list[str] = field(default_factory=list)
    lint_tools: list[str] = field(default_factory=list)
    type_tools: list[str] = field(default_factory=list)


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
    entry_points: list[str] = []
    manifests: list[str] = []
    test_tools: list[str] = []
    lint_tools: list[str] = []
    type_tools: list[str] = []

    if package:
        languages.append("Node.js")
        if (root / "pnpm-lock.yaml").exists():
            package_manager = "pnpm"
        elif (root / "yarn.lock").exists():
            package_manager = "yarn"
        elif (root / "bun.lockb").exists() or (root / "bun.lock").exists():
            package_manager = "bun"
        else:
            package_manager = "npm"
        manifests.append("package.json")

    if (root / "pyproject.toml").exists() or (root / "requirements.txt").exists() or any(root.glob("*.py")):
        languages.append("Python")
        package_manager = package_manager or ("uv" if (root / "uv.lock").exists() else "pip")
        manifests.extend(name for name in ("pyproject.toml", "requirements.txt", "poetry.lock", "uv.lock") if (root / name).exists())

    if (root / "go.mod").exists() or any(root.glob("*.go")):
        languages.append("Go")
        package_manager = package_manager or "go modules"
        manifests.append("go.mod")
        test_tools.append("go test")
        lint_tools.append("go vet")

    java_manifest = next((name for name in ("pom.xml", "build.gradle", "build.gradle.kts") if (root / name).exists()), None)
    if java_manifest or any(root.rglob("*.java")):
        languages.append("Java")
        manifests.extend([java_manifest] if java_manifest else [])
        package_manager = package_manager or ("maven" if java_manifest == "pom.xml" else "gradle")
        test_tools.append("mvn test" if package_manager == "maven" else "gradle test")

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
        type_tools.append("tsc")

    scripts = package.get("scripts", {}) if isinstance(package.get("scripts"), dict) else {}
    if "test" in scripts:
        test_tools.append("npm test")
    if "lint" in scripts:
        lint_tools.append("npm run lint")
    if "typecheck" in scripts:
        type_tools.append("npm run typecheck")

    req_text = ""
    if (root / "requirements.txt").exists():
        req_text = (root / "requirements.txt").read_text(encoding="utf-8", errors="ignore").lower()
    if "fastapi" in req_text:
        frameworks.append("FastAPI")
    if "flask" in req_text:
        frameworks.append("Flask")
    if (root / "manage.py").exists() or "django" in req_text:
        frameworks.append("Django")

    pyproject_text = (root / "pyproject.toml").read_text(encoding="utf-8", errors="ignore").lower() if (root / "pyproject.toml").exists() else ""
    if "pytest" in req_text or "pytest" in pyproject_text or (root / "tests").exists():
        test_tools.append("pytest")
    if "ruff" in pyproject_text:
        lint_tools.append("ruff")
    if "mypy" in pyproject_text:
        type_tools.append("mypy")
    if "pyright" in pyproject_text:
        type_tools.append("pyright")

    for name in ("main.py", "app.py", "manage.py", "src/main.py", "src/index.ts", "src/index.js", "cmd/main.go"):
        if (root / name).exists():
            entry_points.append(name)
    source_dirs = [name for name in ("src", "app", "lib", "cmd", "internal") if (root / name).is_dir()]
    test_dirs = [name for name in ("tests", "test", "spec", "__tests__") if (root / name).is_dir()]

    if "Expo" in frameworks and "React Native" in frameworks:
        primary = "React Native / Expo"
    elif "Next.js" in frameworks:
        primary = "Next.js"
    elif "React" in frameworks:
        primary = "React"
    elif len(languages) > 1:
        primary = "Mixed: " + ", ".join(languages)
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
        scripts=scripts,
        entry_points=_unique(entry_points),
        source_dirs=_unique(source_dirs),
        test_dirs=_unique(test_dirs),
        manifests=_unique([item for item in manifests if item]),
        test_tools=_unique(test_tools),
        lint_tools=_unique(lint_tools),
        type_tools=_unique(type_tools),
    )


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
