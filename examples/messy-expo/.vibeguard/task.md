# Implementation Plan

## Goal
Add OTP login without changing existing architecture.

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
