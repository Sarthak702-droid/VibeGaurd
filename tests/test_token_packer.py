from pathlib import Path

from vibeguard.core.scanner import scan_project
from vibeguard.core.token_packer import pack_files


def test_pack_prioritizes_goal_relevant_auth_and_login_files(tmp_path: Path) -> None:
    (tmp_path / "src" / "screens").mkdir(parents=True)
    (tmp_path / "src" / "services").mkdir(parents=True)
    (tmp_path / "src" / "screens" / "Login.tsx").write_text("OTP login screen", encoding="utf-8")
    (tmp_path / "src" / "services" / "auth.ts").write_text("verify otp phone auth", encoding="utf-8")
    (tmp_path / "src" / "screens" / "Dashboard.tsx").write_text("chart settings reports", encoding="utf-8")
    (tmp_path / "package.json").write_text('{"dependencies":{"expo":"latest"}}', encoding="utf-8")

    scan = scan_project(tmp_path)
    result = pack_files(tmp_path, scan, "add OTP login", max_tokens=80)

    included = [item.path for item in result.included]

    assert "src/services/auth.ts" in included
    assert "src/screens/Login.tsx" in included
    assert "package.json" in included
    assert "src/screens/Dashboard.tsx" not in included
    assert result.estimated_tokens <= 80

