from __future__ import annotations

import tomllib
from pathlib import Path

from vibeguard import __version__


ROOT = Path(__file__).parent.parent


def load_pyproject() -> dict:
    with (ROOT / "pyproject.toml").open("rb") as file:
        return tomllib.load(file)


def test_build_metadata_is_consistent() -> None:
    data = load_pyproject()

    assert data["build-system"] == {
        "requires": ["hatchling>=1.26"],
        "build-backend": "hatchling.build",
    }
    assert data["project"]["name"] == "vibegaurd-cli"
    assert data["project"]["version"] == __version__ == "0.2.0"
    assert data["project"]["requires-python"] == ">=3.11"


def test_console_scripts_are_exact() -> None:
    scripts = load_pyproject()["project"]["scripts"]

    assert scripts == {
        "vibeguard": "vibeguard.cli:app",
        "vig": "vibeguard.cli:app",
        "vbg": "vibeguard.cli:app",
    }


def test_hatch_build_targets_include_package_and_release_files() -> None:
    data = load_pyproject()
    targets = data["tool"]["hatch"]["build"]["targets"]

    assert targets["wheel"]["packages"] == ["vibeguard"]
    assert {"vibeguard", "tests", "README.md", "LICENSE", "pyproject.toml"} <= set(
        targets["sdist"]["include"]
    )


def test_publish_workflow_uses_named_pypi_secret() -> None:
    workflow = (ROOT / ".github" / "workflows" / "publish.yml").read_text(encoding="utf-8")

    assert "password: ${{ secrets.PYPI_API_TOKEN }}" in workflow
    assert "user: __token__" in workflow
    assert "id-token: write" not in workflow
    assert "pypi-AgEI" not in workflow


def test_local_environment_files_are_gitignored() -> None:
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()

    assert ".env" in gitignore
    assert ".env.*" in gitignore
