from pathlib import Path

from vibeguard.core.builders import build_context
from vibeguard.core.detector import ProjectDetection
from vibeguard.core.scanner import ScanResult
from vibeguard.core.token_packer import PackResult


def _scan() -> ScanResult:
    return ScanResult(
        root=Path("demo"),
        detection=ProjectDetection(
            primary_type="React Native / Expo",
            languages=["Node.js"],
            frameworks=["React", "React Native", "Expo", "TypeScript"],
            package_manager="npm",
        ),
        files=["package.json", "src/screens/Login.tsx", "src/services/auth.ts"],
        important_files=["package.json", "tsconfig.json", "src/screens/Login.tsx", "src/services/auth.ts"],
    )


def test_context_explains_project_and_architecture_rules() -> None:
    content = build_context(_scan(), "add OTP login", PackResult())

    assert "## Project Type\nReact Native / Expo" in content
    assert "Auth service exists at src/services/auth.ts" in content
    assert "Do not rewrite the full project." in content


def test_context_lists_do_not_touch_rules() -> None:
    content = build_context(_scan(), "add OTP login", PackResult())

    assert "## Do-Not-Touch Rules" in content
    assert "Do not modify lock files unless dependency changes are required." in content
