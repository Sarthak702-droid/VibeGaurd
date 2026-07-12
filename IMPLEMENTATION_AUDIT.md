# VibeGuard Master-Prompt Implementation Audit

Audit date: 2026-07-12
Source of truth: `/home/sarthaktripathy/Downloads/master prompt`
Previous audit reviewed: `/home/sarthaktripathy/Downloads/done`

## Executive verdict

The repository is a functional local pre/post coding MVP, not yet the universal
agent execution and governance layer described by the master prompt. The existing
64-test suite passes, but the baseline Ruff run reports 12 unused-import errors.
The previous `done` report is directionally accurate, although every claim below
has been checked against the local repository rather than accepted verbatim.

## What is implemented

| Area | Evidence | Status |
|---|---|---|
| Package foundation | Hatchling package, Python 3.11+, Typer/Rich CLI, `vibeguard` and `vbg` entry points | Partial |
| Initialization | Creates `.vibeguard/`, config, cache/report folders and starter artifacts | Partial |
| Repository scanning | Ignores generated/binary/sensitive files, detects Python/Node and common frameworks | Partial |
| Context packing | Relevance score and approximate token budget | Partial |
| Planning/prompting | Markdown plan, prompt, context and pack generation | Partial |
| Optional GLM | NVIDIA OpenAI-compatible prompt refinement with graceful errors | Partial |
| Verification | Python and npm command runners with an allowlist | Partial |
| Git diff | Tracked/untracked diff extraction and basic file statistics | Partial |
| Risk checks | Basic path, large-diff, dependency, deletion, missing-test and secret rules | Partial |
| Reports | Markdown verification, diff, risk and next-prompt artifacts | Partial |
| Doctor | Basic OS, tools, project and installation diagnostics | Partial |
| Tests | 64 existing tests pass in `.venv` | Complete for old MVP only |

## What is missing or incomplete

| Master-prompt phase | Gap |
|---|---|
| 1 — Foundation | Primary `vig` command, modular command/service boundary, structured logging, consistent branding |
| 2 — Configuration | Typed schema, `.vibeguard.yml`, global config, env overrides, validation and `config show/set/validate` |
| 3 — Scanner | Java/Go/mixed support, entry points, source/test dirs, tool and manifest discovery, architecture summary |
| 4 — Snapshot | Persisted Git/file-hash baseline and separation of pre-existing vs session changes |
| 5 — Intelligence | Provider interface and plan/diff/risk/next methods; current GLM helper only rewrites prompts |
| 6 — Context | Selected file contents, selection reasons, robust redaction, output/budget/task options |
| 7 — Planning | Generic structured plan; current implementation contains Expo/Login/OTP assumptions |
| 8 — Prompt | Agent adapters, allowed/prohibited scope and completion contract |
| 9 — Agents | Registry, detection, metadata, versions and six adapters |
| 10 — Runner | Preflight, safe interactive subprocess, signals, timeout, session metadata and postflight |
| 11 — Monitoring | Auditable session records and baseline comparison |
| 12 — Verification | Auto-detection beyond Python/npm, modes/JSON, duration/output fields and failing CLI exit code |
| 13 — Risk | 0–100 scoring, INFO–CRITICAL, policy thresholds and broader deterministic rules |
| 14 — Secrets/deps | Dedicated commands, line/remediation output, optional Gitleaks and manifest-diff analysis |
| 15 — Explain | Business/security/compatibility/test-impact explanation command |
| 16 — Reports | Consolidated terminal/Markdown/JSON/SARIF report and final decision |
| 17 — Next | Uses actual check failures, files, protected scope, tests and acceptance criteria |
| 18 — Doctor | Agent, config, credentials, Gitleaks/Semgrep, type tools and cache checks |
| 19 — CI/pre-commit | GitHub/GitLab generation, CI check and hook installation |
| 20 — Shell | Interactive guarded workflow |

## Technical debt and blockers

- Public naming is inconsistent: `VibeGuard`, `vibegaurd-cli`, `VibeGuard`,
  `vibeguard`, and `vbg`.
- Business logic and presentation are concentrated in `vibeguard/cli.py`.
- Configuration is generated but not loaded by the scanner, verifier, or policy
  engine.
- Context and plan output contains project-specific Expo/OTP text.
- Verification treats missing tools as skipped but does not make all blocking
  failures produce a non-zero CLI result.
- The current product is observability and verification, not OS-level isolation;
  it must not be described as a security sandbox.
- External credentials are optional; deterministic/local-only behavior must remain
  fully usable.

## Implementation sequence

1. Preserve compatibility while adding the `vig` entry point and typed config.
2. Generalize repository/context/planning and introduce persisted snapshots.
3. Add LLM and coding-agent adapter interfaces.
4. Add safe runner, session monitor and postflight workflow.
5. Upgrade verification, deterministic security, secrets and dependencies.
6. Add explain/report/next, doctor, CI/pre-commit and the interactive shell.
7. Add phase-focused tests, documentation and package quality gates.

## Baseline verification

- `.venv/bin/python -m pytest -q`: **64 passed**.
- `.venv/bin/ruff check .`: **failed with 12 F401 findings** (eight in legacy
  tests and four re-export warnings in `vibeguard/utils/__init__.py`).
- Git working tree was clean before this audit.
