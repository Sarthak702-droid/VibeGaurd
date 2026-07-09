from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from pathlib import Path

from vibeguard.core.detector import ProjectDetection, detect_project


DEFAULT_IGNORES = {
    ".git",
    ".vibeguard",
    ".next",
    ".expo",
    ".venv",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    "coverage",
}
IMPORTANT_NAMES = {
    "package.json",
    "app.json",
    "app.config.js",
    "tsconfig.json",
    "pyproject.toml",
    "requirements.txt",
    "README.md",
    "src/screens/Login.tsx",
    "src/services/auth.ts",
}

BINARY_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp",
    ".mp4", ".mov", ".avi", ".pdf", ".zip",
    ".tar", ".gz", ".exe", ".dll", ".so",
    ".dylib", ".class", ".jar", ".ico"
}

SENSITIVE_PATTERNS = {
    ".env", ".env.local", ".env.production", ".env.development", ".env.test",
    "*.pem", "*.key", "*.p12", "*.pfx", "id_rsa", "id_ed25519",
    "credentials.json", "service-account.json"
}

def is_sensitive(name: str) -> bool:
    for pattern in SENSITIVE_PATTERNS:
        if fnmatch.fnmatch(name, pattern) or fnmatch.fnmatch(name.lower(), pattern.lower()):
            return True
    return False

@dataclass(frozen=True)
class ScanResult:
    root: Path
    detection: ProjectDetection
    files: list[str] = field(default_factory=list)
    important_files: list[str] = field(default_factory=list)
    ignored: list[str] = field(default_factory=list)
    skipped_symlinks: list[str] = field(default_factory=list)
    large_files: list[str] = field(default_factory=list)
    sensitive_files: list[str] = field(default_factory=list)


def scan_project(root: Path) -> ScanResult:
    root = Path(root).resolve()
    files: list[str] = []
    ignored: set[str] = set()
    skipped_symlinks: list[str] = []
    large_files: list[str] = []
    sensitive_files: list[str] = []

    for path in root.rglob("*"):
        rel = path.relative_to(root).as_posix()
        
        # 1. Symlink Safety
        if path.is_symlink():
            skipped_symlinks.append(rel)
            continue
            
        parts = set(path.relative_to(root).parts)
        ignored_part = parts.intersection(DEFAULT_IGNORES)
        if ignored_part:
            ignored.update(ignored_part)
            continue
            
        if path.is_dir():
            continue
            
        # 2. Sensitive Files (Exclude content scan, list as sensitive)
        if is_sensitive(path.name):
            sensitive_files.append(rel)
            continue
            
        # 3. Binary File Handling
        if path.suffix.lower() in BINARY_SUFFIXES:
            continue
            
        # 4. File Size Limits (1 MB)
        try:
            size = path.stat().st_size
        except OSError:
            size = 0
            
        if size > 1_048_576:
            large_files.append(rel)
            # still include path metadata
            files.append(rel)
            continue

        files.append(rel)

    important = [file for file in files if file in IMPORTANT_NAMES or Path(file).name in IMPORTANT_NAMES]
    return ScanResult(
        root=root,
        detection=detect_project(root),
        files=sorted(files),
        important_files=sorted(set(important)),
        ignored=sorted(ignored),
        skipped_symlinks=sorted(skipped_symlinks),
        large_files=sorted(large_files),
        sensitive_files=sorted(sensitive_files),
    )


