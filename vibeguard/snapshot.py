"""Repository baseline capture used to attribute changes to agent sessions."""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from vibeguard.core.report_generator import ensure_vibeguard_dir
from vibeguard.core.scanner import scan_project


@dataclass(frozen=True)
class Snapshot:
    snapshot_id: str
    created_at: str
    commit: str | None
    branch: str | None
    status: list[str]
    hashes: dict[str, str] = field(default_factory=dict)
    agent: str | None = None
    task: str | None = None


@dataclass(frozen=True)
class SnapshotChanges:
    added: list[str] = field(default_factory=list)
    modified: list[str] = field(default_factory=list)
    deleted: list[str] = field(default_factory=list)

    @property
    def files(self) -> list[str]:
        return sorted(self.added + self.modified + self.deleted)


def _git(root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False)
    except FileNotFoundError:
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def _hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def capture_snapshot(root: Path, *, agent: str | None = None, task: str | None = None) -> Snapshot:
    root = root.resolve()
    scan = scan_project(root)
    hashes: dict[str, str] = {}
    for relative in scan.files:
        path = root / relative
        if relative in scan.large_files or not path.is_file():
            continue
        try:
            hashes[relative] = _hash(path)
        except OSError:
            continue
    created = datetime.now(UTC).isoformat()
    identity = hashlib.sha256(f"{created}:{agent}:{task}".encode()).hexdigest()[:12]
    status_text = _git(root, "status", "--porcelain=v1", "--untracked-files=all") or ""
    return Snapshot(
        snapshot_id=identity,
        created_at=created,
        commit=_git(root, "rev-parse", "HEAD"),
        branch=_git(root, "branch", "--show-current"),
        status=status_text.splitlines(),
        hashes=hashes,
        agent=agent,
        task=task,
    )


def save_snapshot(root: Path, snapshot: Snapshot) -> Path:
    directory = ensure_vibeguard_dir(root) / "cache" / "snapshots"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{snapshot.snapshot_id}.json"
    path.write_text(json.dumps(asdict(snapshot), indent=2), encoding="utf-8")
    return path


def compare_snapshot(root: Path, before: Snapshot) -> SnapshotChanges:
    after = capture_snapshot(root, agent=before.agent, task=before.task)
    before_paths = set(before.hashes)
    after_paths = set(after.hashes)
    return SnapshotChanges(
        added=sorted(after_paths - before_paths),
        modified=sorted(path for path in before_paths & after_paths if before.hashes[path] != after.hashes[path]),
        deleted=sorted(before_paths - after_paths),
    )
