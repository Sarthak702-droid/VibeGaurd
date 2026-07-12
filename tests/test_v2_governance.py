from __future__ import annotations

import json
import subprocess
from pathlib import Path

from typer.testing import CliRunner

from vibeguard.agents import ADAPTERS, AgentAdapter
from vibeguard.cli import app
from vibeguard.config import default_config, load_config, set_config_value, write_project_config
from vibeguard.core.detector import detect_project
from vibeguard.governance_report import build_report, write_report
from vibeguard.security import Finding, decision_for, risk_score, scan_secrets
from vibeguard.snapshot import capture_snapshot, compare_snapshot, save_snapshot


runner = CliRunner()


def test_typed_config_round_trip_and_environment_override(tmp_path: Path, monkeypatch) -> None:
    write_project_config(tmp_path, default_config(tmp_path))
    set_config_value(tmp_path, "policies.blocking_score", "70")
    monkeypatch.setenv("VIBEGUARD_DEFAULT_AGENT", "claude")

    config = load_config(tmp_path)

    assert config.project.name == tmp_path.name
    assert config.policies.blocking_score == 70
    assert config.agents.default == "claude"
    assert "NVIDIA_API_KEY" not in (tmp_path / ".vibeguard.yml").read_text(encoding="utf-8")


def test_detector_supports_go_java_and_mixed_repositories(tmp_path: Path) -> None:
    (tmp_path / "go.mod").write_text("module example.test/demo\n", encoding="utf-8")
    (tmp_path / "pom.xml").write_text("<project />", encoding="utf-8")
    (tmp_path / "main.go").write_text("package main", encoding="utf-8")

    result = detect_project(tmp_path)

    assert result.languages == ["Go", "Java"]
    assert result.primary_type == "Mixed: Go, Java"
    assert result.package_manager == "go modules"
    assert {"go.mod", "pom.xml"} <= set(result.manifests)


def test_snapshot_attributes_only_changes_after_baseline(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    existing = tmp_path / "existing.py"
    existing.write_text("before = True\n", encoding="utf-8")
    baseline = capture_snapshot(tmp_path, agent="mock", task="change file")
    path = save_snapshot(tmp_path, baseline)
    existing.write_text("before = False\n", encoding="utf-8")
    (tmp_path / "new.py").write_text("created = True\n", encoding="utf-8")

    changes = compare_snapshot(tmp_path, baseline)

    assert path.exists()
    assert changes.modified == ["existing.py"]
    assert changes.added == ["new.py"]


def test_agent_adapter_builds_argument_array_without_shell(monkeypatch) -> None:
    adapter = AgentAdapter("mock", "mock-agent", "Mock Agent", ("--task",))
    monkeypatch.setattr("vibeguard.agents.shutil.which", lambda executable: "/usr/bin/mock-agent")

    assert adapter.build_command("safe task", ["--flag"]) == [
        "/usr/bin/mock-agent",
        "--task",
        "safe task",
        "--flag",
    ]


def test_antigravity_adapter_uses_real_chat_subcommand(monkeypatch) -> None:
    monkeypatch.setattr("vibeguard.agents.shutil.which", lambda executable: "/usr/bin/antigravity")

    assert ADAPTERS["antigravity"].build_command("review safely") == [
        "/usr/bin/antigravity",
        "chat",
        "review safely",
    ]


def test_secret_scan_redacts_value_and_risk_decision(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text('api_key = "sk-live-1234567890abcdef"\n', encoding="utf-8")

    findings = scan_secrets(tmp_path)

    assert len(findings) == 1
    assert "1234567890abcdef" not in findings[0].message
    assert "[REDACTED]" in findings[0].message
    assert risk_score(findings) == 50
    assert decision_for(50) == "PASS_WITH_WARNINGS"
    assert decision_for(80) == "BLOCKED"


def test_reports_serialize_markdown_json_and_sarif(tmp_path: Path) -> None:
    finding = Finding("policy", "HIGH", "Protected path modified.", "auth/login.py", 3)
    report = build_report(
        tmp_path,
        findings=[finding],
        checks=[{"name": "tests", "status": "Passed", "details": "ok"}],
        files_changed=["auth/login.py"],
        agent="mock",
        task="secure login",
    )

    markdown = write_report(tmp_path, report, "markdown")
    json_path = write_report(tmp_path, report, "json")
    sarif = write_report(tmp_path, report, "sarif")

    assert "PASS_WITH_WARNINGS" in markdown.read_text(encoding="utf-8")
    assert json.loads(json_path.read_text(encoding="utf-8"))["agent"] == "mock"
    assert json.loads(sarif.read_text(encoding="utf-8"))["version"] == "2.1.0"


def test_cli_init_config_agents_and_unknown_exec(tmp_path: Path) -> None:
    init_result = runner.invoke(app, ["init", "--project", str(tmp_path), "--no-banner"])
    validate_result = runner.invoke(app, ["config", "validate", "--project", str(tmp_path)])
    agents_result = runner.invoke(app, ["agents", "list"])
    exec_result = runner.invoke(app, ["exec", "--project", str(tmp_path), "--", "unknown-agent"])

    assert init_result.exit_code == 0
    assert (tmp_path / ".vibeguard.yml").exists()
    assert validate_result.exit_code == 0
    assert "PASS" in validate_result.output
    assert agents_result.exit_code == 0
    assert "OpenAI Codex" in agents_result.output
    assert exec_result.exit_code == 2
    assert "Unknown agent" in exec_result.output
