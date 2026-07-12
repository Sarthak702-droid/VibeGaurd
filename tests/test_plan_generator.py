from pathlib import Path

from vibeguard.core.builders import build_plan
from vibeguard.core.detector import ProjectDetection
from vibeguard.core.scanner import ScanResult


def _scan() -> ScanResult:
    return ScanResult(root=Path("demo"), detection=ProjectDetection(primary_type="React Native / Expo"))


def test_plan_generator_creates_task_specific_scope() -> None:
    content = build_plan(_scan(), "add OTP login without changing architecture")

    assert "## Objective" in content
    assert "## Required Work" in content
    assert "## Security Considerations" in content
    assert "## Estimated Risk\nHigh" in content


def test_plan_generator_keeps_non_auth_tasks_small() -> None:
    content = build_plan(_scan(), "fix button spacing")

    assert "smallest reviewable diff" in content
    assert "## Files That Must Not Change Without Approval" in content
