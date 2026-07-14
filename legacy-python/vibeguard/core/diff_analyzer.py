from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class ChangedFile:
    path: str
    status: str
    additions: int = 0
    deletions: int = 0


@dataclass(frozen=True)
class DiffSummary:
    changed_files: list[ChangedFile] = field(default_factory=list)
    raw_diff: str = ""
    status: str = "ok"  # "git_missing", "not_git_repo", "no_commits", "ok"


def analyze_diff(root: Path) -> DiffSummary:
    root = Path(root)
    
    if not shutil.which("git"):
        return DiffSummary(status="git_missing")
        
    res = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=root, capture_output=True, text=True, check=False)
    if res.returncode != 0 or res.stdout.strip() != "true":
        return DiffSummary(status="not_git_repo")
        
    res_head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=False)
    if res_head.returncode != 0:
        return DiffSummary(status="no_commits")

    raw_diff = _git(root, ["diff", "HEAD", "--", "."])
    numstat = _git(root, ["diff", "HEAD", "--numstat", "--", "."])
    name_status = _git(root, ["diff", "HEAD", "--name-status", "--", "."])
    additions_by_file: dict[str, tuple[int, int]] = {}

    for line in numstat.splitlines():
        parts = line.split("\t")
        if len(parts) == 3:
            add = int(parts[0]) if parts[0].isdigit() else 0
            delete = int(parts[1]) if parts[1].isdigit() else 0
            additions_by_file[parts[2]] = (add, delete)

    changed: list[ChangedFile] = []
    for line in name_status.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            status = _status_name(parts[0])
            path = parts[-1]
            additions, deletions = additions_by_file.get(path, (0, 0))
            changed.append(ChangedFile(path=path, status=status, additions=additions, deletions=deletions))

    tracked = {item.path for item in changed}
    untracked = _git(root, ["ls-files", "--others", "--exclude-standard"])
    for path in untracked.splitlines():
        if not path or path in tracked or path == ".vibeguard" or path.startswith(".vibeguard/"):
            continue
        absolute = root / path
        try:
            text = absolute.read_text(encoding="utf-8", errors="ignore") if absolute.stat().st_size <= 1_048_576 else ""
        except OSError:
            text = ""
        additions = len(text.splitlines())
        changed.append(ChangedFile(path=path, status="added", additions=additions))
        if text:
            raw_diff += f"\ndiff --git a/{path} b/{path}\n--- /dev/null\n+++ b/{path}\n"
            raw_diff += "\n".join(f"+{line}" for line in text.splitlines()) + "\n"

    return DiffSummary(changed_files=changed, raw_diff=raw_diff, status="ok")


def _git(root: Path, args: list[str]) -> str:
    try:
        result = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False)
    except FileNotFoundError:
        return ""
    return result.stdout


def _status_name(code: str) -> str:
    if code.startswith("A"):
        return "added"
    if code.startswith("D"):
        return "deleted"
    if code.startswith("R"):
        return "renamed"
    return "modified"
