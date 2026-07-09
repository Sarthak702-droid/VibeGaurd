# VibeGuard Context Pack

## Goal
add OTP login without changing existing architecture

## Project Type
React Native / Expo

## Frameworks
React, React Native, Expo, TypeScript

## Package Manager
npm

## Important Files
- app.json
- package.json
- tsconfig.json
- src/screens/Login.tsx
- src/services/auth.ts

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
- Do not rewrite the full project.
- Do not change unrelated files.
- Follow the existing folder structure.
- Keep changes minimal and explainable.
- Add validation.
- Add tests if a test setup exists.
- Explain every changed file.
- Do not expose secrets.
- Do not hardcode API keys.
- Do not change app branding unless required.

## Do-Not-Touch Rules
- Do not modify unrelated screens.
- Do not modify generated files.
- Do not modify lock files unless dependency changes are required.
- Do not modify environment files.
- Do not restructure the project.
