from __future__ import annotations

from vibeguard.core.scanner import ScanResult
from vibeguard.core.token_packer import PackResult


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

## Folder Summary
- `src/screens/` contains app screens.
- `src/services/` contains service/API logic.
- `app.json` contains Expo app configuration.
- `package.json` contains dependencies and scripts.
- `tsconfig.json` contains TypeScript configuration.

## Existing Architecture Notes
- Login screen exists at src/screens/Login.tsx.
- Auth service exists at src/services/auth.ts.
- Existing folder structure should be preserved.
- Login-related UI changes should be made inside the existing Login screen unless a new component is necessary.
- Auth-related logic should use or extend the existing auth service.
- Do not rewrite navigation unless required.
- Do not expose secrets in frontend code.

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
"""


def build_plan(scan: ScanResult, goal: str) -> str:
    if _is_auth_goal(goal):
        return f"""# Implementation Plan

## Goal
{_sentence(goal)}

## Scope
- Update existing Login screen.
- Add phone number input.
- Add OTP request flow.
- Add OTP verification flow.
- Use existing auth service.
- Add loading states.
- Add error states.
- Keep UI changes limited to the login flow.

## Out Of Scope
- Do not rewrite app navigation.
- Do not add a new backend unless required.
- Do not change app branding.
- Do not add payment/subscription logic.
- Do not introduce unrelated state management changes.
- Do not restructure the app.

## Likely Affected Files
- src/screens/Login.tsx
- src/services/auth.ts

## Implementation Steps
1. Inspect the existing Login screen.
2. Inspect the existing auth service.
3. Add or update phone number input.
4. Add OTP request action.
5. Add OTP verification action.
6. Add loading state for OTP request and verification.
7. Add error handling for invalid phone number and invalid OTP.
8. Keep all changes inside the existing login/auth flow.
9. Add or update tests if a test setup exists.
10. Explain all changed files.

## Acceptance Criteria
- User can enter phone number.
- User can request OTP.
- User can enter OTP.
- Invalid OTP shows an error.
- Empty phone number shows validation error.
- Loading state is shown during request.
- Auth logic uses existing auth service.
- No secrets are stored in frontend.
- Existing app architecture is not rewritten.

## Test Cases
- Empty phone number.
- Invalid phone number.
- OTP request success.
- OTP request failure.
- OTP verification success.
- OTP verification failure.
- Network failure during OTP request.
- Network failure during OTP verification.

## Risks
- Auth flow may be changed incorrectly.
- OTP state handling may break login UX.
- Secrets may accidentally be placed in frontend.
- Missing tests may allow silent bugs.
- AI may modify unrelated files.

## Rollback Plan
- Revert changes in src/screens/Login.tsx.
- Revert changes in src/services/auth.ts.
- Remove any newly added OTP-only files if they are not required.
- Re-run VibeGuard verify after rollback.
"""
    return f"""# Implementation Plan

## Goal
{_sentence(goal)}

## Scope
- Implement the smallest change that satisfies the goal.
- Reuse existing project patterns in this {scan.detection.primary_type} project.

## Out Of Scope
- Full rewrites.
- Unrelated UI, navigation, dependency, or architecture changes.
- Secret or environment changes unless explicitly requested.

## Likely Affected Files
{_plain_bullets(scan.important_files[:12] or scan.files[:12])}

## Implementation Steps
1. Inspect relevant files and current tests.
2. Make the focused code change.
3. Add or update tests for changed behavior.
4. Run available verification commands.
5. Explain changed files and known risks.

## Acceptance Criteria
- Goal works end to end.
- Existing behavior remains intact.
- Tests are added or updated where behavior changed.
- No unrelated files are modified.

## Test Cases
- Main success path.
- Empty or invalid input.
- Error response.
- Network or command failure.

## Risks
- AI may modify unrelated files.
- Missing tests may allow silent bugs.

## Rollback Plan
- Revert only files touched for this task.
- Re-run VibeGuard verify after rollback.
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
    return """# Suggested Next Prompt

Review the OTP login implementation.

Focus only on:
- validation
- error handling
- loading states
- tests
- secret leakage

Do not rewrite the architecture.
Do not modify unrelated files.
Do not change navigation unless required.

Add tests for:
- empty phone number
- invalid phone number
- invalid OTP
- successful OTP verification
- failed OTP verification
- network failure during OTP request
- network failure during OTP verification

After making changes, explain:
1. Which files were changed.
2. Why each file was changed.
3. What tests were added.
4. What commands should be run.
5. Any remaining limitations.
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
