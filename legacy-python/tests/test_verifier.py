from pathlib import Path

from vibeguard.core.detector import ProjectDetection
from vibeguard.core.verifier import verify_project


def test_verifier_skips_missing_node_scripts(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text('{"scripts": {"start": "expo start"}}', encoding="utf-8")
    (tmp_path / "tsconfig.json").write_text("{}", encoding="utf-8")
    detection = ProjectDetection(primary_type="React Native / Expo", languages=["Node.js"], scripts={"start": "expo start"})

    report = verify_project(tmp_path, detection)

    assert report.status == "Warning"
    assert any(check.name == "test" and check.status == "Skipped" for check in report.checks)
    assert any(check.name == "lint" and check.status == "Skipped" for check in report.checks)
    assert any(check.name == "typecheck" and check.status == "Skipped" for check in report.checks)


def test_verifier_passes_detected_node_config_files(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text('{"scripts": {}}', encoding="utf-8")
    (tmp_path / "tsconfig.json").write_text("{}", encoding="utf-8")
    detection = ProjectDetection(primary_type="React Native / Expo", languages=["Node.js"], scripts={})

    report = verify_project(tmp_path, detection)

    assert any(check.name == "package.json detected" and check.status == "Passed" for check in report.checks)
    assert any(check.name == "TypeScript project detected" and check.status == "Passed" for check in report.checks)
