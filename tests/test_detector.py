from pathlib import Path

from vibeguard.core.detector import detect_project


def test_detects_expo_react_native_typescript_project(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        """
        {
          "scripts": {"test": "jest", "lint": "eslint ."},
          "dependencies": {
            "expo": "latest",
            "react-native": "latest",
            "react": "latest"
          },
          "devDependencies": {"typescript": "latest"}
        }
        """,
        encoding="utf-8",
    )
    (tmp_path / "app.json").write_text("{}", encoding="utf-8")
    (tmp_path / "tsconfig.json").write_text("{}", encoding="utf-8")

    result = detect_project(tmp_path)

    assert result.primary_type == "React Native / Expo"
    assert "Node.js" in result.languages
    assert "React Native" in result.frameworks
    assert "Expo" in result.frameworks
    assert "TypeScript" in result.frameworks
    assert result.package_manager == "npm"

