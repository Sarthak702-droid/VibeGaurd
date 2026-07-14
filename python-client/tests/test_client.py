from __future__ import annotations

import stat
from pathlib import Path

import pytest

from vibegaurd_client.client import VibeGaurdClient


def _backend(tmp_path: Path) -> Path:
    executable = tmp_path / "backend"
    executable.write_text("#!/bin/sh\nprintf '%s\\n' \"$@\"\n", encoding="utf-8")
    executable.chmod(executable.stat().st_mode | stat.S_IXUSR)
    return executable


def test_scans_local_repository_with_argument_array(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    result = VibeGaurdClient(_backend(tmp_path)).scan_local(repository)
    assert result.args[:3] == ("scan", str(repository.resolve()), "--format")
    assert "scan" in result.stdout


def test_rejects_non_github_or_credentialed_urls(tmp_path: Path) -> None:
    client = VibeGaurdClient(_backend(tmp_path))
    with pytest.raises(ValueError):
        client.scan_public_github("https://token@github.com/owner/repo.git")
    with pytest.raises(ValueError):
        client.scan_public_github("https://gitlab.com/owner/repo.git")


def test_public_github_scan_is_non_interactive(tmp_path: Path) -> None:
    result = VibeGaurdClient(_backend(tmp_path)).scan_public_github("https://github.com/owner/repo.git")
    assert result.args == ("scan", "https://github.com/owner/repo.git", "--format", "json", "--non-interactive")
