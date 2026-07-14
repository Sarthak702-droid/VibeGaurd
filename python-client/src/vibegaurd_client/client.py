"""A small, dependency-free adapter around the Rust VibeGuard binary.

The package is intentionally not a second scanner. It validates inputs and
invokes the Rust backend using an argument array, never a shell string.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import PurePath
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.parse import ParseResult, urlparse


class BackendNotFoundError(RuntimeError):
    """Raised when the Rust VibeGuard binary cannot be found."""


class CommandError(RuntimeError):
    """Raised when the Rust backend returns a non-zero result."""

    def __init__(self, result: "CommandResult") -> None:
        super().__init__(result.stderr or f"VIBEGAURD backend exited with {result.returncode}")
        self.result = result


@dataclass(frozen=True)
class CommandResult:
    """Structured result returned by the Rust backend."""

    args: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str

    def json(self) -> Mapping[str, Any]:
        """Decode JSON output, raising a clear error when another format was used."""
        try:
            parsed = json.loads(self.stdout)
        except json.JSONDecodeError as error:
            raise ValueError("The Rust backend did not return JSON output.") from error
        if not isinstance(parsed, dict):
            raise ValueError("The Rust backend returned JSON that is not an object.")
        return parsed


class VibeGaurdClient:
    """Use a local Rust backend to scan local or public GitHub repositories."""

    def __init__(self, binary: str | os.PathLike[str] | None = None, *, timeout: float = 60) -> None:
        self._binary = self._resolve_binary(binary)
        if timeout <= 0:
            raise ValueError("timeout must be greater than zero")
        self._timeout = timeout

    @property
    def binary(self) -> Path:
        """Resolved Rust backend executable."""
        return self._binary

    @staticmethod
    def _resolve_binary(binary: str | os.PathLike[str] | None) -> Path:
        explicit = binary or os.environ.get("VIBEGAURD_BINARY")
        if explicit:
            path = Path(explicit).expanduser()
            if path.is_file():
                return path.resolve()
            resolved = shutil.which(str(path))
            if resolved:
                return Path(resolved)
            raise BackendNotFoundError(f"Configured Rust backend was not found: {path}")

        for candidate in ("VIBEGAURD", "vibeguard", "vbg"):
            resolved = shutil.which(candidate)
            if resolved:
                return Path(resolved)
        raise BackendNotFoundError(
            "Rust VibeGuard backend not found. Install the Rust binary or set VIBEGAURD_BINARY."
        )

    def run(self, arguments: Sequence[str], *, check: bool = True) -> CommandResult:
        """Run an allowed Rust CLI argument sequence without invoking a shell."""
        if not arguments:
            raise ValueError("at least one backend argument is required")
        result = subprocess.run(
            [str(self._binary), *arguments],
            check=False,
            shell=False,
            text=True,
            capture_output=True,
            timeout=self._timeout,
        )
        completed = CommandResult(
            args=tuple(str(item) for item in arguments),
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
        )
        if check and completed.returncode != 0:
            raise CommandError(completed)
        return completed

    def scan_local(
        self,
        repository: str | os.PathLike[str],
        *,
        output_format: str = "json",
        refresh: bool = False,
    ) -> CommandResult:
        """Scan a local repository, including one cloned/pulled by the user."""
        path = Path(repository).expanduser()
        if not path.is_dir():
            raise ValueError(f"local repository directory does not exist: {path}")
        arguments = ["scan", str(path.resolve()), "--format", output_format]
        if refresh:
            arguments.append("--refresh")
        return _materialize_report(self.run(arguments))

    def scan_public_github(
        self,
        repository_url: str,
        *,
        reference: str | None = None,
        output_format: str = "json",
        refresh: bool = False,
    ) -> CommandResult:
        """Safely scan a public HTTPS GitHub repository through the Rust backend."""
        parsed = _validate_public_github_url(repository_url)
        normalized = parsed.geturl()
        arguments = ["scan", normalized, "--format", output_format, "--non-interactive"]
        if reference:
            arguments.extend(["--reference", reference])
        if refresh:
            arguments.append("--refresh")
        return _materialize_report(self.run(arguments))


def _validate_public_github_url(value: str) -> ParseResult:
    parsed = urlparse(value)
    if parsed.scheme != "https" or parsed.hostname != "github.com":
        raise ValueError("public GitHub scans require an https://github.com/owner/repository URL")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("repository URLs must not contain credentials, query parameters, or fragments")
    segments = [segment for segment in parsed.path.split("/") if segment]
    if len(segments) != 2 or any(segment in {".", ".."} for segment in segments):
        raise ValueError("repository URL must contain exactly an owner and repository name")
    return parsed


def _materialize_report(result: CommandResult) -> CommandResult:
    """Return report content when the Rust CLI writes a machine-readable file.

    The Rust CLI reports its output path on stdout for file formats. Reading that
    local path gives Python callers the requested JSON/Markdown/SARIF directly,
    while preserving the original backend result when no report exists.
    """
    prefix = "Report written: "
    for line in result.stdout.splitlines():
        if line.startswith(prefix):
            path = Path(PurePath(line.removeprefix(prefix)))
            try:
                content = path.read_text(encoding="utf-8")
            except OSError:
                return result
            return CommandResult(
                args=result.args,
                returncode=result.returncode,
                stdout=content,
                stderr=result.stderr,
            )
    return result
