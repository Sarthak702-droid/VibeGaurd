from __future__ import annotations

import subprocess
from pathlib import Path

from typer.testing import CliRunner

from vibeguard.cli import app


runner = CliRunner()


def _make_expo_project(root: Path) -> Path:
    project = root / "messy-expo"
    (project / "src" / "screens").mkdir(parents=True)
    (project / "src" / "services").mkdir(parents=True)
    (project / "src" / "navigation").mkdir(parents=True)
    (project / "package.json").write_text(
        """
        {
          "name": "messy-expo-demo",
          "private": true,
          "scripts": {"start": "expo start"},
          "dependencies": {
            "expo": "latest",
            "react": "latest",
            "react-native": "latest"
          },
          "devDependencies": {"typescript": "latest"}
        }
        """,
        encoding="utf-8",
    )
    (project / "app.json").write_text('{"expo":{"name":"MessyExpoDemo"}}', encoding="utf-8")
    (project / "tsconfig.json").write_text('{"compilerOptions":{"strict":true}}', encoding="utf-8")
    (project / "src" / "screens" / "Login.tsx").write_text("Login screen phone password", encoding="utf-8")
    (project / "src" / "services" / "auth.ts").write_text("auth login user phone verify", encoding="utf-8")
    (project / "src" / "navigation" / "AppNavigator.tsx").write_text("navigation login route", encoding="utf-8")
    return project


def test_context_command_writes_required_project_context(tmp_path: Path) -> None:
    project = _make_expo_project(tmp_path)

    result = runner.invoke(
        app,
        ["context", "--project", str(project), "--goal", "add OTP login without changing existing architecture"],
    )

    assert result.exit_code == 0
    assert "Context written:" in result.output
    content = (project / ".vibeguard" / "context.md").read_text(encoding="utf-8")
    assert "# VibeGuard Context Pack" in content
    assert "## Project Type\nReact Native / Expo" in content
    assert "## Frameworks\nReact, React Native, Expo, TypeScript" in content
    assert "## Folder Summary" in content
    assert "## Existing Architecture Notes" in content
    assert "## AI Rules" in content
    assert "## Do-Not-Touch Rules" in content


def test_plan_command_writes_auth_specific_task_plan(tmp_path: Path) -> None:
    project = _make_expo_project(tmp_path)

    result = runner.invoke(app, ["plan", "--project", str(project), "add OTP login without changing existing architecture"])

    assert result.exit_code == 0
    assert "Plan written:" in result.output
    content = (project / ".vibeguard" / "task.md").read_text(encoding="utf-8")
    assert content.startswith("# Implementation Plan")
    assert "## Scope" in content
    assert "- Update existing Login screen." in content
    assert "## Likely Affected Files" in content
    assert "- src/screens/Login.tsx" in content
    assert "## Test Cases" in content
    assert "- OTP verification failure." in content
    assert "## Rollback Plan" in content


def test_pack_command_writes_token_saving_pack(tmp_path: Path) -> None:
    project = _make_expo_project(tmp_path)

    result = runner.invoke(app, ["pack", "--project", str(project), "--goal", "add OTP login", "--max-tokens", "8000"])

    assert result.exit_code == 0
    assert "Pack written:" in result.output
    assert "Estimated tokens:" in result.output
    content = (project / ".vibeguard" / "pack.md").read_text(encoding="utf-8")
    assert "# VibeGuard Token-Saving Pack" in content
    assert "## Max Token Budget\n8000" in content
    assert "- package.json" in content
    assert "- app.json" in content
    assert "- tsconfig.json" in content
    assert "- src/screens/Login.tsx" in content
    assert "- src/services/auth.ts" in content
    assert "## Relevance Rules Used" in content
    assert "- phone" in content


def test_verify_command_skips_missing_node_scripts_and_writes_report(tmp_path: Path) -> None:
    project = _make_expo_project(tmp_path)

    result = runner.invoke(app, ["verify", "--project", str(project)])

    assert result.exit_code == 0
    assert "test skipped: no test script found" in result.output
    assert "lint skipped: no lint script found" in result.output
    assert "typecheck skipped: no typecheck script found" in result.output
    content = (project / ".vibeguard" / "reports" / "verification_report.md").read_text(encoding="utf-8")
    assert "package.json detected" in content
    assert "TypeScript project detected" in content


def test_diff_risks_and_next_prompt_use_git_changes(tmp_path: Path) -> None:
    project = _make_expo_project(tmp_path)
    subprocess.run(["git", "init"], cwd=project, check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=project, check=True, capture_output=True)
    subprocess.run(
        ["git", "-c", "user.name=Demo", "-c", "user.email=demo@example.com", "commit", "-m", "baseline"],
        cwd=project,
        check=True,
        capture_output=True,
    )
    (project / "src" / "services" / "auth.ts").write_text(
        'const apiKey = "sk_live_demo"; export async function verifyOtp() {}',
        encoding="utf-8",
    )

    diff_result = runner.invoke(app, ["diff-explain", "--project", str(project)])
    risks_result = runner.invoke(app, ["risks", "--project", str(project)])
    next_result = runner.invoke(app, ["next-prompt", "--project", str(project)])

    assert diff_result.exit_code == 0
    assert "Auth-related file changed" in diff_result.output
    assert "No test file changed" in diff_result.output
    assert risks_result.exit_code == 0
    assert "Risk Level:" in risks_result.output
    assert "auth-related files require manual review" in risks_result.output
    assert next_result.exit_code == 0
    diff_report = (project / ".vibeguard" / "reports" / "diff_report.md").read_text(encoding="utf-8")
    risk_report = (project / ".vibeguard" / "reports" / "risk_report.md").read_text(encoding="utf-8")
    next_prompt = (project / ".vibeguard" / "reports" / "next_prompt.md").read_text(encoding="utf-8")
    assert "## Detected Risk Notes" in diff_report
    assert "Auth-related file changed." in diff_report
    assert "## Overall Risk Level" in risk_report
    assert "Reason: auth-related files require manual review" in risk_report
    assert next_prompt.startswith("# Suggested Next Prompt")
    assert "Do not rewrite the architecture." in next_prompt
    assert "failed OTP verification" in next_prompt



def test_doctor_reports_project_readiness_with_missing_scripts(tmp_path: Path) -> None:
    project = _make_expo_project(tmp_path)
    (project / ".vibeguard" / "reports").mkdir(parents=True)
    subprocess.run(["git", "init"], cwd=project, check=True, capture_output=True)

    result = runner.invoke(app, ["doctor", "--project", str(project)])

    assert result.exit_code == 0
    assert "VibeGuard Doctor" in result.output
    assert "OK Git repository detected" in result.output
    assert "OK package.json detected" in result.output
    assert "OK TypeScript project detected" in result.output
    assert "OK .vibeguard folder detected" in result.output
    assert "OK reports folder detected" in result.output
    assert "OK Project type detected: React Native / Expo" in result.output
    assert "OK Package manager detected: npm" in result.output
    assert "WARNING test script missing" in result.output
    assert "WARNING lint script missing" in result.output
    assert "WARNING typecheck script missing" in result.output
    assert "Status: Ready with warnings" in result.output


def test_all_command_runs_complete_workflow(tmp_path: Path) -> None:
    project = _make_expo_project(tmp_path)
    subprocess.run(["git", "init"], cwd=project, check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=project, check=True, capture_output=True)
    subprocess.run(
        ["git", "-c", "user.name=Demo", "-c", "user.email=demo@example.com", "commit", "-m", "baseline"],
        cwd=project,
        check=True,
        capture_output=True,
    )

    result = runner.invoke(
        app,
        ["all", "--project", str(project), "--goal", "add OTP login without changing existing architecture"],
    )

    assert result.exit_code == 0
    assert "Running VibeGuard workflow..." in result.output
    assert "OK scan completed" in result.output
    assert "OK context generated" in result.output
    assert "OK plan generated" in result.output
    assert "OK prompt generated" in result.output
    assert "OK pack generated" in result.output
    assert "verify completed" in result.output
    assert "OK diff report generated" in result.output
    assert "OK risk report generated" in result.output
    assert "OK next prompt generated" in result.output
    assert "Workflow complete." in result.output
    assert (project / ".vibeguard" / "context.md").exists()
    assert (project / ".vibeguard" / "task.md").exists()
    assert (project / ".vibeguard" / "prompt.md").exists()
    assert (project / ".vibeguard" / "pack.md").exists()
    assert (project / ".vibeguard" / "reports" / "verification_report.md").exists()
    assert (project / ".vibeguard" / "reports" / "diff_report.md").exists()
    assert (project / ".vibeguard" / "reports" / "risk_report.md").exists()
    assert (project / ".vibeguard" / "reports" / "next_prompt.md").exists()

