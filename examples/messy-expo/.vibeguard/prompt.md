# AI Coding Task

You are working inside an existing codebase.

## Goal
add OTP login without changing existing architecture

## Rules
- `Do not rewrite the full project.`
- `Do not change unrelated files.`
- `Follow the existing folder structure.`
- `Keep changes minimal and explainable.`
- `Add validation.`
- `Add tests if a test setup exists.`
- `Explain every changed file.`
- `Do not expose secrets.`
- `Do not hardcode API keys.`
- `Do not change app branding unless required.`

## Project Context
- Type: React Native / Expo
- Frameworks: React, React Native, Expo, TypeScript

## Files To Inspect
- `src/screens/Login.tsx`
- `src/services/auth.ts`
- `src/navigation/AppNavigator.tsx`
- `app.json`
- `tsconfig.json`
- `package.json`

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
