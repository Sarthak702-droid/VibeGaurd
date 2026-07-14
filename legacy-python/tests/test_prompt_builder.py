from pathlib import Path

from vibeguard.core.builders import build_prompt
from vibeguard.core.detector import ProjectDetection
from vibeguard.core.scanner import ScanResult
from vibeguard.core.token_packer import PackedFile, PackResult


def test_prompt_builder_tells_ai_to_avoid_rewrites_and_unrelated_files() -> None:
    scan = ScanResult(root=Path("demo"), detection=ProjectDetection(primary_type="React Native / Expo", frameworks=["React", "Expo"]))
    pack = PackResult(included=[PackedFile(path="src/screens/Login.tsx", score=10, estimated_tokens=10)])

    content = build_prompt(scan, "add OTP login", pack)

    assert "Do not rewrite the full project." in content
    assert "Do not change unrelated files." in content
    assert "`src/screens/Login.tsx`" in content


def test_prompt_builder_requires_change_explanation_and_tests() -> None:
    scan = ScanResult(root=Path("demo"), detection=ProjectDetection(primary_type="React Native / Expo"))
    content = build_prompt(scan, "add OTP login", PackResult())

    assert "Changed files list" in content
    assert "Tests added or updated" in content

