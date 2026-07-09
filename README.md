# VibeGuard

Guardrails for vibe-coded software.

VibeGuard is an open-source Python CLI that helps AI-assisted developers generate clean project context, better prompts, token-aware file packs, verification reports, Git diff explanations, risk reports, and next prompts.

It is not an AI coding agent and it does not require an LLM API key. It sits before and after tools like Codex, Cursor, Claude, ChatGPT, Windsurf, Replit, and similar coding assistants.

## Positioning

Before AI codes, give it the right context.

After AI codes, verify what changed.

Save tokens. Catch risky AI changes. Ship safer.

## Install

### Global Install with pipx (Recommended)

```bash
pipx install vibeguard
```

### Install for Development

```bash
git clone <repo-url>
cd Vibegaurd
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

# CLI Usage

After installation, VibeGuard can be run globally:

```bash
vibeguard
```

or with the short alias:

```bash
vg
```

## Quick Start

```bash
cd my-project
vibeguard init
vibeguard all --goal "add OTP login without changing existing architecture"
```

Short alias:

```bash
cd my-project
vg init
vg all -g "add OTP login without changing existing architecture"
```

## Commands

```bash
vibeguard scan
vibeguard context -g "add OTP login"
vibeguard plan -g "add OTP login"
vibeguard prompt -g "add OTP login"
vibeguard pack -g "add OTP login" -t 8000
vibeguard verify
vibeguard diff-explain
vibeguard risks
vibeguard next-prompt
vibeguard doctor
vibeguard all -g "add OTP login"
```

## Security Defaults

VibeGuard:

* Does not use shell=True
* Does not print secrets
* Skips .env files
* Skips private keys
* Skips binary files
* Does not auto-modify source code
* Does not run destructive commands

## Quick Demo

Run VibeGuard on the included messy Expo project:

```bash
vibeguard scan --project examples/messy-expo
vibeguard doctor --project examples/messy-expo
vibeguard all --project examples/messy-expo --goal "add OTP login without changing existing architecture"
```

Sample scan output:

```text
Project type: React Native / Expo
Package manager: npm
Frameworks: React, React Native, Expo, TypeScript
```

Sample pack output:

```text
Pack written: examples/messy-expo/.vibeguard/pack.md
Estimated tokens: 387 / 8000
```

Sample risk output after a risky auth change:

```text
Risk Level: High
WARNING Secret-like string found
Reason: changed code contains possible hardcoded secret/API key/token
WARNING Auth logic changed
File: src/services/auth.ts
Reason: auth-related files require manual review
WARNING No test file changed
Reason: feature code changed without test update
```

## Core Workflow

Before asking an AI tool to code:

```bash
vibeguard scan
vibeguard context --goal "add OTP login"
vibeguard plan "add OTP login without changing existing architecture"
vibeguard prompt "add OTP login without changing existing architecture"
vibeguard pack --goal "add OTP login" --max-tokens 8000
```

After AI changes code:

```bash
vibeguard verify
vibeguard diff-explain
vibeguard risks
vibeguard next-prompt
```

For demos and repeated local use, run the complete MVP flow:

```bash
vibeguard all --goal "add OTP login without changing existing architecture"
```

Generated files live in `.vibeguard/`:

```text
.vibeguard/
├── context.md
├── prompt.md
├── task.md
├── pack.md
├── cache/
└── reports/
    ├── diff_report.md
    ├── next_prompt.md
    ├── risk_report.md
    └── verification_report.md
```

For real user projects, keep generated cache and reports out of Git:

```gitignore
.vibeguard/cache/
.vibeguard/reports/
```

## Commands

- `vibeguard init` creates `.vibeguard/`.
- `vibeguard scan` detects stack, frameworks, important files, and ignored folders.
- `vibeguard doctor` checks whether the project is ready for VibeGuard.
- `vibeguard context --goal "..."` writes `.vibeguard/context.md`.
- `vibeguard plan "..."` writes `.vibeguard/task.md`.
- `vibeguard prompt "..."` writes `.vibeguard/prompt.md`.
- `vibeguard pack --goal "..." --max-tokens 8000` selects relevant files.
- `vibeguard verify` runs available Python/Node checks and skips unavailable tools.
- `vibeguard diff-explain` summarizes the current Git diff.
- `vibeguard risks` detects risky patterns in changed files.
- `vibeguard next-prompt` generates a follow-up prompt for hardening changes.
- `vibeguard all --goal "..."` runs the complete MVP workflow.

## Demo Video Script

1. Show `examples/messy-expo`.
2. Run `vibeguard scan --project examples/messy-expo`.
3. Run `vibeguard all --project examples/messy-expo --goal "add OTP login without changing existing architecture"`.
4. Open `.vibeguard/prompt.md`.
5. Make a small risky change in `src/services/auth.ts`.
6. Run `vibeguard risks --project examples/messy-expo`.
7. Show auth risk, secret-like string detection, and missing test warning.
8. End with: "Save tokens. Catch risky AI changes. Ship safer."

## Roadmap

v0.1.0:

- scan
- context
- plan
- prompt
- pack
- verify
- diff-explain
- risks
- next-prompt
- doctor
- all

v0.2.0:

- JSON output mode
- better secret detection
- better test detection
- GitHub Actions support
- custom config rules

v0.3.0:

- PR review mode
- HTML report
- framework-specific packs
- better dependency graph
