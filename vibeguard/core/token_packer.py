from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from vibeguard.core.scanner import ScanResult


RELATED_TERMS = {
    "login": {"auth", "user", "phone", "otp", "session", "token", "signin", "sign-in"},
    "otp": {"login", "auth", "phone", "verify", "verification", "code"},
    "auth": {"login", "session", "token", "jwt", "user", "permission"},
    "test": {"spec", "test", "jest", "pytest"},
}
CONFIG_FILES = {"package.json", "pyproject.toml", "requirements.txt", "app.json", "tsconfig.json"}


@dataclass(frozen=True)
class PackedFile:
    path: str
    score: int
    estimated_tokens: int


@dataclass(frozen=True)
class PackResult:
    included: list[PackedFile] = field(default_factory=list)
    excluded: list[PackedFile] = field(default_factory=list)
    estimated_tokens: int = 0


def pack_files(root: Path, scan: ScanResult, goal: str, max_tokens: int = 8000) -> PackResult:
    keywords = _goal_keywords(goal)
    scored: list[PackedFile] = []
    for rel_path in scan.files:
        path = Path(root) / rel_path
        
        is_large = False
        if hasattr(scan, 'large_files') and rel_path in scan.large_files:
            is_large = True
        else:
            try:
                if path.stat().st_size > 1_048_576:
                    is_large = True
            except OSError:
                pass

        if is_large:
            text = ""
        else:
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                text = ""
                
        score = _score_file(rel_path, text, keywords)
        tokens = max(1, len(text) // 4)
        scored.append(PackedFile(rel_path, score, tokens))

    ordered = sorted(scored, key=lambda item: (-item.score, item.estimated_tokens, item.path))
    included: list[PackedFile] = []
    excluded: list[PackedFile] = []
    total = 0
    for item in ordered:
        if item.score < 3:
            excluded.append(item)
            continue
        if total + item.estimated_tokens <= max_tokens:
            included.append(item)
            total += item.estimated_tokens
        else:
            excluded.append(item)

    return PackResult(included=included, excluded=excluded, estimated_tokens=total)


def _goal_keywords(goal: str) -> set[str]:
    base = {word.lower() for word in re.findall(r"[a-zA-Z][a-zA-Z0-9_-]+", goal)}
    expanded = set(base)
    for word in base:
        expanded.update(RELATED_TERMS.get(word, set()))
    return expanded


def _score_file(rel_path: str, text: str, keywords: set[str]) -> int:
    lower_path = rel_path.lower()
    lower_text = text.lower()
    score = 0
    for keyword in keywords:
        if keyword in lower_path:
            score += 5
        if keyword in lower_text:
            score += 3
    if Path(rel_path).name in CONFIG_FILES:
        score += 4
    if any(part in lower_path for part in ("screen", "service", "route", "api", "navigation")):
        score += 2
    if len(text) > 20_000:
        score -= 5
    return score

