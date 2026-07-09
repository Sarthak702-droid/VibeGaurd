from pathlib import Path

from vibeguard.core.scanner import scan_project


def test_scan_ignores_generated_folders_and_finds_important_files(tmp_path: Path) -> None:
    (tmp_path / "src" / "screens").mkdir(parents=True)
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "dist").mkdir()
    (tmp_path / "package.json").write_text('{"dependencies":{"expo":"latest"}}', encoding="utf-8")
    (tmp_path / "app.json").write_text("{}", encoding="utf-8")
    (tmp_path / "src" / "screens" / "Login.tsx").write_text("export default function Login() {}", encoding="utf-8")
    (tmp_path / "node_modules" / "ignored.js").write_text("ignored", encoding="utf-8")
    (tmp_path / "dist" / "bundle.js").write_text("ignored", encoding="utf-8")

    result = scan_project(tmp_path)

    assert "package.json" in result.important_files
    assert "app.json" in result.important_files
    assert "src/screens/Login.tsx" in result.files
    assert "node_modules/ignored.js" not in result.files
    assert "dist/bundle.js" not in result.files
    assert "node_modules" in result.ignored

