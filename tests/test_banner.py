import os
from pathlib import Path
from rich.console import Console
import yaml
from vibeguard.ui.banner import print_banner


def test_print_banner_not_crash(capsys) -> None:
    console = Console()
    print_banner(console, compact=False)
    captured = capsys.readouterr()
    assert "VibeGuard" in captured.out
    assert "Guardrails for vibe-coded software" in captured.out


def test_print_banner_compact(capsys) -> None:
    console = Console()
    print_banner(console, compact=True)
    captured = capsys.readouterr()
    assert "VibeGuard" in captured.out
    assert "Guardrails for vibe-coded software" in captured.out


def test_banner_disabled_env(capsys, monkeypatch) -> None:
    monkeypatch.setenv("VIBEGUARD_NO_BANNER", "1")
    console = Console()
    print_banner(console, compact=False)
    captured = capsys.readouterr()
    assert captured.out == ""


def test_banner_disabled_config(tmp_path, capsys, monkeypatch) -> None:
    monkeypatch.delenv("VIBEGUARD_NO_BANNER", raising=False)

    vg_dir = tmp_path / ".vibeguard"
    vg_dir.mkdir(parents=True)
    config_file = vg_dir / "config.yaml"

    config_data = {
        "ui": {
            "show_banner": False
        }
    }
    with open(config_file, "w", encoding="utf-8") as f:
        yaml.safe_dump(config_data, f)

    console = Console()
    print_banner(console, compact=False, project=tmp_path)
    captured = capsys.readouterr()
    assert captured.out == ""


def test_banner_enabled_config(tmp_path, capsys, monkeypatch) -> None:
    monkeypatch.delenv("VIBEGUARD_NO_BANNER", raising=False)

    vg_dir = tmp_path / ".vibeguard"
    vg_dir.mkdir(parents=True)
    config_file = vg_dir / "config.yaml"

    config_data = {
        "ui": {
            "show_banner": True
        }
    }
    with open(config_file, "w", encoding="utf-8") as f:
        yaml.safe_dump(config_data, f)

    console = Console()
    print_banner(console, compact=False, project=tmp_path)
    captured = capsys.readouterr()
    assert "VibeGuard" in captured.out
