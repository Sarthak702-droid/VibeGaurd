import tomllib
from pathlib import Path
from typer.testing import CliRunner
from vibeguard.cli import app


def test_vbg_alias_registered_in_pyproject() -> None:
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)
    assert data["project"]["name"] == "vibegaurd-cli"
    scripts = data.get("project", {}).get("scripts", {})
    assert "vibeguard" in scripts
    assert "vbg" in scripts
    assert "vg" not in scripts
    assert scripts["vibeguard"] == "vibeguard.cli:app"
    assert scripts["vbg"] == "vibeguard.cli:app"


def test_readme_uses_distribution_and_vbg_alias() -> None:
    readme = (Path(__file__).parent.parent / "README.md").read_text(encoding="utf-8")
    assert "pipx install vibegaurd-cli" in readme
    assert "vig init" in readme
    assert "vg init" not in readme


def test_vibeguard_help_does_not_crash() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Trust, verification, and governance" in result.output


def test_prompt_help_describes_opt_in_llm() -> None:
    result = CliRunner().invoke(app, ["prompt", "--help"])

    assert result.exit_code == 0
    assert "--llm" in result.output
    assert "NVIDIA_API_KEY" in result.output


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
    assert "vbg command:" in result.output


def test_doctor_explains_linux_vg_conflict(tmp_path, monkeypatch) -> None:
    (tmp_path / "package.json").write_text('{"dependencies": {}}', encoding="utf-8")
    monkeypatch.setattr("vibeguard.cli.get_os_name", lambda: "linux")
    commands = {
        "vibeguard": "/tmp/vibeguard",
        "vbg": "/tmp/vbg",
        "vg": "/usr/bin/vg",
    }
    monkeypatch.setattr("vibeguard.cli.shutil.which", commands.get)

    runner = CliRunner()
    result = runner.invoke(app, ["doctor", "-p", str(tmp_path), "--no-banner"])

    assert result.exit_code == 0
    assert "WARNING: Linux already provides a system command named 'vg'." in result.output
    assert "Use 'vbg' instead." in result.output
