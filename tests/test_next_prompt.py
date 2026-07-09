from vibeguard.core.builders import build_next_prompt


def test_next_prompt_focuses_on_hardening_risky_changes() -> None:
    content = build_next_prompt(["HIGH Secret-like string found", "MEDIUM No test file changed"])

    assert content.startswith("# Suggested Next Prompt")
    assert "Do not rewrite the architecture." in content
    assert "secret leakage" in content
    assert "invalid OTP" in content
