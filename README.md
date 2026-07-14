# VibeGuard

VibeGuard is a fast, local-first Rust guardrail for AI-assisted software development. It scans repositories without executing their code, builds bounded context packs and offline plans/prompts, explains Git changes, detects risks and secret-like values, runs requested verification, and emits Markdown, JSON, and SARIF reports.

The production CLI is Rust-native: no Python, pip, virtual environment, server, LLM API, or internet connection is required for local use.

## Python client package

For Python application integration, use the separate `vibegaurd-rust-client`
distribution in [`python-client/`](python-client/). Its import package is
`vibegaurd_client`, and its installed console command is exactly `VIBEGAURD`.
It is a thin adapter—not a second scanner—and invokes the Rust binary through a
safe argument array.

```bash
pip install vibegaurd-rust-client
VIBEGAURD scan-local ../repository-already-pulled-by-user
VIBEGAURD scan-github https://github.com/owner/public-repository.git
```

Set `VIBEGAURD_BINARY=/path/to/vibeguard` when the Rust backend is not on
`PATH`. Public GitHub scans only accept credential-free `https://github.com/...`
URLs; local scans use a user-supplied existing directory.

## Install

```bash
cargo install --path crates/vibeguard-cli
```

The only installed executables are `vibeguard` and `vbg`. `vg` is intentionally not provided because it conflicts with an existing Linux command. The former Python `vig` alias is a documented migration break and is not installed.

## Quick start

```bash
vibeguard init
vibeguard scan .
vibeguard context --goal "Add OTP login" --max-tokens 8000
vibeguard plan --goal "Add OTP login"
vibeguard prompt --goal "Add OTP login" --agent codex
vibeguard risk
vibeguard secrets
vibeguard verify
vibeguard report --format sarif --output vibeguard.sarif
```

`vbg` runs the same command implementation.

## Remote repositories

```bash
vibeguard scan https://github.com/owner/repo.git
vibeguard scan git@github.com:company/private-repo.git
vibeguard scan https://gitlab.com/group/repo.git --ref develop
```

Remote scans use a per-user bare Git cache and read committed Git objects; they do not check out, execute, install, or build repository code. Git prompts are disabled, SSH uses batch mode with a connection timeout, submodules and Git LFS objects are not fetched by default, and dangerous transports (`ext::`, custom helpers, and remote `file:` URLs) are rejected.

Private repositories use the existing SSH agent/configuration and Git credential helper. `vibeguard auth status` shows non-secret diagnostics and `vibeguard auth login github` explains how to reuse GitHub CLI credentials. A `VIBEGUARD_GIT_TOKEN` is detected for CI but is never printed, written into a URL, or placed in process arguments.

## Configuration

Create `.vibeguard.toml` with `vibeguard config init`. Precedence is command arguments, supported environment overrides, project config, user config, then built-in defaults. Unknown TOML keys are rejected.

## Security model

Scanning is read-only and does not execute Git hooks or repository content. Sensitive paths, binaries, generated/vendor content, and oversized files are skipped and counted. Secret evidence is redacted. Verification is a separate, explicit command and executes direct argument arrays only—never shell strings.

## Reports and exit codes

`scan` and `report` support `terminal`, `json`, `markdown`, and `sarif` output. Machine-readable formats include a schema version. Exit codes are stable:

- `0`: success
- `1`: findings/check threshold exceeded
- `2`: invalid input or configuration
- `3`: authentication or authorization failure
- `4`: Git/network failure
- `5`: verification failure
- `6`: unsupported environment or repository
- `7`: internal VibeGuard error

## Migration from Python

The pre-migration Python implementation and its tests are retained under `legacy-python/` for behavior comparisons during the transition. They are not a runtime dependency of the Rust CLI. See [the migration audit](docs/MIGRATION_AUDIT.md) and ADRs in `docs/adr/` for the compatibility matrix and design decisions.
