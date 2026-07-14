from __future__ import annotations

import re

from vibeguard.core.scanner import ScanResult
from vibeguard.core.token_packer import PackResult, pack_files


RULES = [
    "Do not rewrite the full project.",
    "Do not change unrelated files.",
    "Follow the existing folder structure.",
    "Keep changes minimal and explainable.",
    "Add validation.",
    "Add tests if a test setup exists.",
    "Explain every changed file.",
    "Do not expose secrets.",
    "Do not hardcode API keys.",
    "Do not change app branding unless required.",
]


def build_context(scan: ScanResult, goal: str, pack: PackResult | None = None) -> str:
    important = _ordered_important_files(scan)
    selected = pack.included if pack else []
    selection = "\n".join(f"- `{item.path}` — {item.reason}" for item in selected) or "- None"
    excerpts: list[str] = []
    for item in selected:
        path = scan.root / item.path
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        excerpts.append(f"### `{item.path}`\nReason: {item.reason}\n\n```text\n{_redact_context(text)[:12000]}\n```")
    source_dirs = ", ".join(scan.detection.source_dirs) or "None detected"
    test_dirs = ", ".join(scan.detection.test_dirs) or "None detected"
    return f"""# VibeGuard Context Pack

## Goal
{goal}

## Project Type
{scan.detection.primary_type}

## Frameworks
{", ".join(scan.detection.frameworks) or "None detected"}

## Package Manager
{scan.detection.package_manager or "Unknown"}

## Important Files
{_plain_bullets(important)}

## Selected Files and Reasons
{selection}

## Folder Summary
- Source directories: {source_dirs}
- Test directories: {test_dirs}
- Entry points: {", ".join(scan.detection.entry_points) or "None detected"}
- Dependency manifests: {", ".join(scan.detection.manifests) or "None detected"}

## Existing Architecture Notes
- Primary type: {scan.detection.primary_type}.
- Languages: {", ".join(scan.detection.languages) or "Unknown"}.
- Preserve established source, test, and configuration conventions.
- Inspect interfaces and tests before changing implementations.

## AI Rules
{_plain_bullets(RULES)}

## Do-Not-Touch Rules
- Do not modify unrelated screens.
- Do not modify generated files.
- Do not modify lock files unless dependency changes are required.
- Do not modify environment files.
- Do not restructure the project.

## Security Notes
- Environment files are intentionally excluded.
- Secrets are not included in this context pack.
- Do not hardcode API keys or tokens.
- Do not expose backend secrets in frontend code.

## Redacted File Context
{chr(10).join(excerpts) if excerpts else "No file content selected."}
"""


def build_plan(scan: ScanResult, goal: str) -> str:
    relevant = pack_files(scan.root, scan, goal, 4000).included
    likely_files = [item.path for item in relevant[:12]] or scan.important_files[:12] or scan.files[:12]
    protected = [".env*", ".github/workflows/", "migrations/", "unrelated source and test files"]
    risk = "High" if _is_auth_goal(goal) or any(term in goal.lower() for term in ("payment", "permission", "migration", "security")) else "Medium"
    return f"""# Implementation Plan

## Objective
{_sentence(goal)}

## Assumptions
- The existing {scan.detection.primary_type} architecture and public interfaces remain authoritative.
- The task should be implemented with the smallest reviewable diff.
- Required tools or credentials not present in the repository will be reported, not invented.

## Scope
- Implement only behavior explicitly required by the objective.
- Reuse existing interfaces, schemas, dependencies, and test patterns.
- Treat selected files as predictions; inspect imports before editing.

## Required Work
- Inspect the likely affected files and their callers.
- Implement the objective with validation and explicit error handling.
- Add or update automated tests for changed behavior.
- Run detected verification commands and explain the final diff.

## Optional Work
- Refactoring is optional and must be limited to code directly blocking the objective.
- New dependencies are optional only when the existing stack cannot satisfy the requirement.

## Likely Affected Files
{_plain_bullets(likely_files)}

## Files That Must Not Change Without Approval
{_plain_bullets(protected)}

## Implementation Steps
1. Inspect relevant interfaces, implementations, configuration, and tests.
2. Confirm the minimal file scope and acceptance criteria.
3. Implement the main success path and input validation.
4. Handle expected failures without leaking sensitive data.
5. Add or update tests for success, invalid input, and failure paths.
6. Run tests, lint, type checks, security checks, and diff review.

## Security Considerations
- Do not add credentials, tokens, or private data to source or generated prompts.
- Preserve authentication, authorization, permission, and validation boundaries.
- Review dependency, configuration, CI, migration, and protected-path changes explicitly.

## Test Plan
- Cover the primary success path.
- Cover empty, malformed, boundary, and unauthorized input where applicable.
- Cover dependency, network, subprocess, or persistence failures where applicable.
- Add a regression test for the behavior being changed.

## Verification Plan
- Run `vig verify --full`.
- Run `vig secrets`, `vig deps`, and `vig risk`.
- Review `vig explain` and generate `vig report`.

## Acceptance Criteria
- The objective works end to end.
- Existing behavior and public interfaces remain compatible unless change is explicit.
- Automated tests cover changed behavior and pass.
- No unrelated or protected files are modified.
- No secret-like values are introduced.

## Estimated Risk
{risk}

## Rollback Considerations
- Revert only files attributed to this task or agent session.
- Restore dependency/lockfile changes together when applicable.
- Re-run verification after rollback.
"""


def build_pack(scan: ScanResult, goal: str, pack: PackResult, max_tokens: int) -> str:
    included = [item.path for item in pack.included]
    excluded = sorted(set(scan.ignored + [item.path for item in pack.excluded] + ["node_modules", ".git", ".vibeguard", "assets", "dist", "build"]))
    keywords = ["login", "auth", "otp", "user", "phone", "verify"] if _is_auth_goal(goal) else sorted(set(goal.lower().split()))
    
    sensitive_lines = []
    if hasattr(scan, "sensitive_files") and scan.sensitive_files:
        for f in scan.sensitive_files:
            sensitive_lines.append(f"Sensitive file skipped: {f}\nReason: secrets must not be included in AI context")
    sensitive_str = "\n\n".join(sensitive_lines) if sensitive_lines else "None"
    
    return f"""# VibeGuard Token-Saving Pack

## Goal
{goal}

## Max Token Budget
{max_tokens}

## Estimated Tokens
{pack.estimated_tokens} / {max_tokens}

## Included Files
{_plain_bullets(included)}

## Excluded Files
{_plain_bullets(excluded)}

## Sensitive Files Excluded
{sensitive_str}

## Relevance Rules Used
Goal keywords:
{_plain_bullets(keywords)}

Files were included if:
- Path matched goal keywords.
- Content matched goal keywords.
- File was an important config file.
- File was detected as important by project scanner.

Files were excluded if:
- File or folder matched ignore rules.
- File was generated or build output.
- File was binary or asset-heavy.
- File was unrelated to the goal.

## AI Usage Notes
Use this pack when asking an AI coding tool to implement the task.
Do not paste the entire repository unless required.
Start with these included files first.
"""


def build_prompt(scan: ScanResult, goal: str, pack: PackResult) -> str:
    return f"""# AI Coding Task

You are working inside an existing codebase.

## Goal
{goal}

## Rules
{_code_bullets(RULES)}

## Project Context
- Type: {scan.detection.primary_type}
- Frameworks: {", ".join(scan.detection.frameworks) or "None detected"}

## Files To Inspect
{_code_bullets([item.path for item in pack.included])}

## Files Not To Touch Without Approval
- `.env*`
- package lockfiles unless dependency work is explicitly required
- migrations
- unrelated screens, routes, navigation, payment, billing, and admin files

## Implementation Steps
1. Read the listed files first.
2. Describe the minimal implementation approach.
3. Change only files needed for the goal.
4. Add or update tests.
5. Run verification.

## Acceptance Criteria
- The goal is implemented with minimal surface area.
- Risky auth/security changes are explained.
- Tests cover success and failure paths.

## Required Output
1. Changed files list
2. Explanation of each change
3. Tests added or updated
4. Commands to run
5. Known limitations
"""


def build_next_prompt(risk_lines: list[str]) -> str:
    findings = _plain_bullets(risk_lines)
    return f"""# Suggested Next Prompt

Correct only the unresolved deterministic findings below.

## Exact Findings
{findings}

## Required Corrections
- Resolve the root cause of each finding without suppressing safety checks.
- Add validation and explicit error handling where the finding identifies missing coverage.
- Remove and revoke any exposed credential; never print its original value.

## Scope Guardrails
- Do not rewrite the architecture.
- Do not modify unrelated or protected files.
- Do not change dependencies, CI, migrations, authentication, or permissions unless a listed finding requires it.

## Tests To Run
- Add a regression test for each corrected behavior.
- Run the affected test suite, lint, type checks, and `vig verify`.
- Run `vig secrets`, `vig deps`, and `vig risk`.

## Acceptance Criteria
- All listed findings are resolved or explicitly documented for human review.
- Blocking checks pass.
- No new high or critical finding is introduced.

## Completion Report
1. List each changed file and why it changed.
2. List tests added or updated and commands executed.
3. Report remaining limitations and unresolved findings.
"""


def _plain_bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "- None"


def _code_bullets(items: list[str]) -> str:
    return "\n".join(f"- `{item}`" if not item.startswith("-") else item for item in items) if items else "- None"


def _ordered_important_files(scan: ScanResult) -> list[str]:
    preferred = ["app.json", "package.json", "tsconfig.json", "src/screens/Login.tsx", "src/services/auth.ts"]
    ordered = [path for path in preferred if path in scan.important_files]
    ordered.extend(path for path in scan.important_files if path not in ordered)
    return ordered


def _is_auth_goal(goal: str) -> bool:
    lower = goal.lower()
    return any(term in lower for term in ("login", "auth", "otp"))


def _sentence(goal: str) -> str:
    text = goal.strip()
    if not text:
        return text
    text = text[0].upper() + text[1:]
    return text if text.endswith(".") else f"{text}."


def _redact_context(text: str) -> str:
    assignment = re.compile(r"(?i)(api[_-]?key|secret|token|password|private[_-]?key)(\s*[:=]\s*)[\"']?[^\s\"']{6,}[\"']?")
    text = assignment.sub(lambda match: f"{match.group(1)}{match.group(2)}[REDACTED]", text)
    text = re.sub(r"(?i)(sk-|ghp_|github_pat_|xoxb-|AIza)[A-Za-z0-9_-]{8,}", "[REDACTED]", text)
    return text
