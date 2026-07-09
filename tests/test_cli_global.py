import tomllib
from pathlib import Path
from typer.testing import CliRunner
from vibeguard.cli import app


def test_vg_alias_registered_in_pyproject() -> None:
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)
    scripts = data.get("project", {}).get("scripts", {})
    assert "vibeguard" in scripts
    assert "vg" in scripts
    assert scripts["vibeguard"] == "vibeguard.cli:app"
    assert scripts["vg"] == "vibeguard.cli:app"


def test_vibeguard_help_does_not_crash() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Guardrails for vibe-coded software" in result.output


def test_default_command_prints_quickstart() -> None:
    runner = CliRunner()
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert "Quick Start Guide" in result.output
    assert "Common commands:" in result.output


def test_project_defaults_to_current_directory(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "package.json").write_text('{"dependencies": {}}', encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(app, ["scan"])
    assert result.exit_code == 0
    assert "Project type:" in result.output


def test_project_short_flag(tmp_path) -> None:
    (tmp_path / "package.json").write_text('{"dependencies": {}}', encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(app, ["scan", "-p", str(tmp_path)])
    assert result.exit_code == 0
    assert "Project type:" in result.output


def test_goal_short_flag(tmp_path) -> None:
    (tmp_path / "package.json").write_text('{"dependencies": {}}', encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(app, ["plan", "-p", str(tmp_path), "-g", "test-goal"])
    assert result.exit_code == 0
    assert "Plan written:" in result.output


def test_max_tokens_short_flag(tmp_path) -> None:
    (tmp_path / "package.json").write_text('{"dependencies": {}}', encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(app, ["context", "-p", str(tmp_path), "-g", "test-goal", "-t", "5000"])
    assert result.exit_code == 0
    assert "Context written:" in result.output


def test_version_flag() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "VibeGuard" in result.output

    result_short = runner.invoke(app, ["-V"])
    assert result_short.exit_code == 0
    assert "VibeGuard" in result_short.output


def test_no_banner_flag(tmp_path) -> None:
    (tmp_path / "package.json").write_text('{"dependencies": {}}', encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(app, ["scan", "-p", str(tmp_path), "--no-banner"])
    assert result.exit_code == 0
    assert "VibeGuard —" not in result.output


def test_doctor_reports_cli_commands(tmp_path) -> None:
    (tmp_path / "package.json").write_text('{"dependencies": {}}', encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(app, ["doctor", "-p", str(tmp_path), "--no-banner"])
    assert result.exit_code == 0
    assert "CLI:" in result.output
    assert "vibeguard command:" in result.output
    assert "vg command:" in result.output
