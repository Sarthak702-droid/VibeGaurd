from vibeguard.core.diff_analyzer import ChangedFile, DiffSummary
from vibeguard.core.risk_engine import analyze_risks


def test_risk_engine_flags_auth_changes_without_tests_and_secret_strings() -> None:
    diff = DiffSummary(
        changed_files=[
            ChangedFile(path="src/services/auth.ts", status="modified", additions=12, deletions=2),
            ChangedFile(path="src/screens/Login.tsx", status="modified", additions=20, deletions=4),
        ],
        raw_diff="+ const apiKey = 'sk_live_1234567890';\n+ async function login() {}",
    )

    report = analyze_risks(diff)

    assert report.overall == "HIGH"
    assert any(r.severity == "MEDIUM" and r.message == "Auth logic changed" for r in report.risks)
    assert any("Secret-like" in r.message for r in report.risks)
    assert any(r.severity == "MEDIUM" and r.message == "No test file changed" for r in report.risks)


def test_risk_engine_does_not_flag_variable_name_without_hardcoded_value() -> None:
    diff = DiffSummary(
        changed_files=[ChangedFile(path="src/services/session.ts", status="modified", additions=3, deletions=0)],
        raw_diff="+ const authToken = getStoredToken();\n+ return authToken;",
    )

    report = analyze_risks(diff)

    assert not any("Secret-like" in r.message for r in report.risks)


def test_risk_engine_flags_hardcoded_secret_patterns() -> None:
    diff = DiffSummary(
        changed_files=[ChangedFile(path="src/services/api.ts", status="modified", additions=1, deletions=0)],
        raw_diff='+ const token = "ghp_1234567890abcdefghijklmnopqrstuv";',
    )

    report = analyze_risks(diff)

    assert any(r.severity == "HIGH" and r.message.startswith("Secret-like string found") for r in report.risks)

