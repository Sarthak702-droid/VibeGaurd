# VibeGuard Python-to-Rust Migration Audit

Audit date: 2026-07-14

## Python implementation inventory

The legacy implementation is a Python 3.11+ Hatch project using Typer, Rich,
Pydantic, PyYAML, PathSpec, Jinja2, and an optional OpenAI-compatible NVIDIA
provider. Its package entrypoint is `vibeguard.cli:app`.

| Python component | Current responsibility | Rust destination | Migration status | Tests required |
|---|---|---|---|---|
| `vibeguard/cli.py` | Typer command routing and terminal output | `vibeguard-cli` | implemented | CLI integration |
| `core/detector.py`, `core/scanner.py` | project and safe file discovery | `vibeguard-scanner` | implemented | scanner unit/integration |
| `core/token_packer.py`, `core/builders.py` | context, plan, prompt, token packing | context/planner/prompt crates | implemented | deterministic snapshots |
| `core/diff_analyzer.py` | working tree Git diff | `vibeguard-git` | implemented | temporary Git repos |
| `core/risk_engine.py`, `security.py` | risk, policy, secret, dependency checks | risk/secrets/deps crates | implemented | rule fixtures |
| `core/verifier.py`, `utils/command_runner.py` | explicit verification process execution | `vibeguard-verifier` | implemented | process tests |
| `governance_report.py`, `core/report_generator.py` | Markdown/JSON/SARIF output | `vibeguard-report` | implemented | serialization snapshots |
| `config.py` | YAML global/project configuration | `vibeguard-config` | implemented with TOML migration | precedence/validation |
| `agents.py`, `snapshot.py` | agent adapters and postflight snapshots | `vibeguard-runner` | implemented | adapter/snapshot tests |
| `intelligence.py`, `llm.py` | optional external AI | `vibeguard-ai` | implemented as offline provider trait | offline fallback |
| `ui/*.py` | banner and quickstart | `vibeguard-cli` | implemented | help/smoke tests |

## Commands and compatibility

| Existing command | Existing options | Existing output | Rust implementation | Compatibility |
|---|---|---|---|---|
| `init` | `--project/-p`, `--no-banner` | `.vibeguard`, `.vibeguard.yml` | init | preserved |
| `scan` | `--project/-p`, `--no-banner` | terminal/cache | scan with positional source and legacy `--project` | extended |
| `context` | goal, `-g/-p/-t`, task, budget, output | `context.md` | context | preserved |
| `plan`, `prompt`, `pack`, `all` | goal/project/token options | Markdown artifacts | same | preserved |
| `verify` | project, quick/full/json | verification report | same | preserved/safer |
| `doctor` | project | system diagnosis | same | Python details removed |
| `diff-explain`, `risks`, `next-prompt` | project | legacy reports | aliases for explain/risk/next | preserved |
| `risk`, `secrets`, `deps`, `explain`, `report`, `next` | project/json/format | terminal and reports | same | preserved/extended |
| `agents`, `run`, `exec`, `shell` | agent/process options | agent session | runner/agents | preserved with allowlist |
| `config show/validate/set` | project/json/key/value | YAML/JSON | config | YAML compatibility + TOML |
| `ci generate/check`, `precommit install` | provider/project | CI or hook | ci/precommit | updated to Rust binary |

The Python package exports `vibeguard`, `vig`, and `vbg`. The Rust release
exports **only** `vibeguard` and `vbg`; `vig` is a documented removed alias and
`vg` is never created because it conflicts with a Linux command.

## Configuration, files, and services

Legacy project configuration is `.vibeguard.yml`, with a legacy
`.vibeguard/config.yaml`; global config is `~/.config/vibeguard/config.yml`.
The Rust implementation writes and validates `.vibeguard.toml`; YAML files stay
available solely in the legacy reference. Existing generated artifacts live in
`.vibeguard/` (reports, cache, sessions, context, plan, prompt, and pack).

The legacy scanner is local-only. It skips symlinks, sensitive names, known
binary suffixes, and files over 1 MiB. It does not have remote ingestion,
repository cache locking, LFS/submodule policy, or content-addressed caching;
these are Rust improvements rather than compatibility regressions.

## Tests, packaging, and workflows discovered

Python has 16 test modules covering CLI flow, scan/detect, context/plan/prompt,
packing, diff/risk, verifier, security, agents, configuration, and packaging.
The sole release workflow (`.github/workflows/publish.yml`) builds and publishes
the Python package to PyPI. It is replaced by Rust CI/release workflows after
parity validation. No pre-existing fixture repository tree or golden baseline
directory exists.
