import os
import subprocess
from pathlib import Path
from unittest import mock
import pytest
from typer.testing import CliRunner

from vibeguard.cli import app, display_path, safe_path
from vibeguard.core.scanner import scan_project
from vibeguard.core.token_packer import pack_files
from vibeguard.core.verifier import verify_project
from vibeguard.core.diff_analyzer import analyze_diff
from vibeguard.core.risk_engine import _redact_secrets_in_line
from vibeguard.core.detector import ProjectDetection
from vibeguard.core.builders import build_pack
from vibeguard.utils.command_runner import run_project_command


runner = CliRunner()


def test_path_handling_windows_style_path():
    p = safe_path("C:\\Users\\name\\Downloads\\Vibegaurd\\examples\\messy-expo")
    # Path will correctly parse it on any OS
    assert p.parts[-1] == "messy-expo"


def test_path_handling_posix_style_path():
    p = Path("/home/user/projects/vibeguard/examples/messy-expo")
    assert p.parts[-1] == "messy-expo"
    assert display_path(p) == str(p)


def test_sensitive_files_are_skipped(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text("SECRET_KEY=supersecret12345", encoding="utf-8")
    
    normal_file = tmp_path / "index.js"
    normal_file.write_text("console.log('hello');", encoding="utf-8")
    
    scan = scan_project(tmp_path)
    
    assert ".env" in scan.sensitive_files
    assert "index.js" in scan.files
    assert ".env" not in scan.files


def test_secret_values_are_redacted():
    line_with_key = "const API_KEY = \"sk-test-1234567890abcdef\";"
    redacted = _redact_secrets_in_line(line_with_key)
    
    assert "sk-test-1234567890abcdef" not in redacted
    assert "[REDACTED]" in redacted
    
    # Standalone test
    line_with_ghp = "my token is ghp_1234567890abcdefghij"
    redacted_ghp = _redact_secrets_in_line(line_with_ghp)
    assert "ghp_1234567890abcdefghij" not in redacted_ghp
    assert "[REDACTED]" in redacted_ghp


def test_shell_true_is_not_used(tmp_path: Path):
    with mock.patch("shutil.which", return_value="/mock/path/pytest"), mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(args=["pytest"], returncode=0, stdout="", stderr="")
        
        # Verify that run_project_command does not pass shell=True
        run_project_command(tmp_path, ["pytest"])
        
        args, kwargs = mock_run.call_args
        assert kwargs.get("shell") is not True


def test_verify_skips_missing_npm(tmp_path: Path):
    (tmp_path / "package.json").write_text('{"dependencies": {}}', encoding="utf-8")
    detection = ProjectDetection(primary_type="Node.js", languages=["Node.js"], scripts={})
    
    with mock.patch("shutil.which", return_value=None):
        report = verify_project(tmp_path, detection)
        # All npm scripts should be skipped because npm is not on PATH
        for check in report.checks:
            if check.name in ("test", "lint", "typecheck"):
                assert check.status == "Skipped"


def test_verify_skips_missing_scripts(tmp_path: Path):
    (tmp_path / "package.json").write_text('{"dependencies": {}}', encoding="utf-8")
    # No test, lint, or typecheck script in ProjectDetection scripts
    detection = ProjectDetection(primary_type="Node.js", languages=["Node.js"], scripts={})
    
    report = verify_project(tmp_path, detection)
    
    # Check they are skipped because they are missing from package.json scripts
    for check in report.checks:
        if check.name in ("test", "lint", "typecheck"):
            assert check.status == "Skipped"
            assert "no" in check.details and "script found" in check.details


def test_git_missing_does_not_crash(tmp_path: Path):
    with mock.patch("shutil.which", return_value=None):
        diff = analyze_diff(tmp_path)
        assert diff.status == "git_missing"
        assert len(diff.changed_files) == 0


def test_not_git_repo_does_not_crash(tmp_path: Path):
    # tmp_path has no .git folder and is not inside any git repo
    diff = analyze_diff(tmp_path)
    assert diff.status == "not_git_repo"


def test_pack_excludes_env_files(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text("SECRET=123", encoding="utf-8")
    
    scan = scan_project(tmp_path)
    pack_res = pack_files(tmp_path, scan, "goal")
    
    included_paths = [item.path for item in pack_res.included]
    assert ".env" not in included_paths
    
    # Verify build_pack shows Sensitive file skipped
    pack_md = build_pack(scan, "goal", pack_res, 8000)
    assert "Sensitive file skipped: .env" in pack_md
    assert "Reason: secrets must not be included in AI context" in pack_md


def test_pack_excludes_binary_files(tmp_path: Path):
    img_file = tmp_path / "logo.png"
    img_file.write_bytes(b"\x89PNG\r\n\x1a\n")
    
    scan = scan_project(tmp_path)
    assert "logo.png" not in scan.files


def test_large_file_is_skipped(tmp_path: Path):
    large_file = tmp_path / "big_data.txt"
    # Write slightly more than 1 MB
    large_file.write_text("a" * (1024 * 1024 + 10), encoding="utf-8")
    
    scan = scan_project(tmp_path)
    assert "big_data.txt" in scan.large_files
    
    pack_res = pack_files(tmp_path, scan, "goal")
    # Verify tokens estimation is handled correctly and no read crash occurred
    assert pack_res is not None


def test_symlink_is_skipped(tmp_path: Path):
    target = tmp_path / "target.txt"
    target.write_text("hello", encoding="utf-8")
    
    link = tmp_path / "link.txt"
    try:
        os.symlink(target, link)
    except OSError:
        pytest.skip("Symlinks are not supported or require admin rights on this system.")
        
    scan = scan_project(tmp_path)
    assert "link.txt" in scan.skipped_symlinks
    assert "link.txt" not in scan.files


def test_doctor_reports_os_and_tools(tmp_path: Path):
    result = runner.invoke(app, ["doctor", "--project", str(tmp_path)])
    
    assert result.exit_code == 0
    assert "VibeGuard Doctor" in result.output
    assert "System:" in result.output
    assert "Tools:" in result.output
    assert "Project:" in result.output
    assert "Security:" in result.output


def test_all_command_runs_workflow(tmp_path: Path):
    # Make a dummy project
    (tmp_path / "package.json").write_text('{"name": "test-project", "scripts": {"test": "echo \'ok\'"}}', encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "index.js").write_text("console.log('hello');", encoding="utf-8")
    
    # Run the "all" command
    result = runner.invoke(app, ["all", "--project", str(tmp_path), "--goal", "refactor index"])
    
    assert result.exit_code == 0
    assert "Running VibeGuard workflow..." in result.output
    assert "OK scan completed" in result.output
    assert "OK context generated" in result.output
    assert "OK plan generated" in result.output
    assert "OK prompt generated" in result.output
    assert "OK pack generated" in result.output
    assert "Workflow complete." in result.output
