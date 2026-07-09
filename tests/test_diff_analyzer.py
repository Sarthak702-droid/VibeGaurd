import subprocess
from pathlib import Path

from vibeguard.core.diff_analyzer import analyze_diff


def test_diff_analyzer_reads_modified_file_from_git_diff(tmp_path: Path) -> None:
    (tmp_path / "file.txt").write_text("one\n", encoding="utf-8")
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "-c", "user.name=Demo", "-c", "user.email=demo@example.com", "commit", "-m", "baseline"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / "file.txt").write_text("one\ntwo\n", encoding="utf-8")

    diff = analyze_diff(tmp_path)

    assert len(diff.changed_files) == 1
    assert diff.changed_files[0].path == "file.txt"
    assert diff.changed_files[0].status == "modified"
    assert "+two" in diff.raw_diff
