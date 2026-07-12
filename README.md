<p align="center">
  <img src="https://raw.githubusercontent.com/Sarthak702-droid/VibeGuard/main/assets/logo.png" alt="VibeGuard Logo" width="500px">
</p>

# VibeGuard

> **Every coding agent helps you write code. VibeGuard helps you ship it safely.**

VibeGuard is a vendor-neutral trust, verification, and governance layer for
AI-assisted software development. It creates repository context and plans before
an agent runs, launches supported coding-agent CLIs through a guarded wrapper,
attributes session changes to a persisted baseline, then verifies and explains
those changes before they ship.

It is **not** a code generator or an OS-level sandbox. Its deterministic workflow
operates locally with no API key. GLM-5.2 intelligence is optional and accessed
through a provider boundary.

---

## 🎯 Positioning

* **Before AI codes:** Supply context packs and optimized prompt templates to maximize coding accuracy.
* **While AI codes:** Run Codex or Antigravity through an auditable session wrapper. Additional adapters are planned after validation.
* **After AI codes:** Instantly verify changes, review Git diff summaries, and catch potential security or logical regressions.
* **Core benefits:** Save context tokens, catch risky AI-generated changes, and ship code with confidence.

---

## 🚀 Installation

### Global Isolated Installation (Recommended)

Install and run VibeGuard globally across all terminal sessions using `pipx`:

```bash
pipx install vibegaurd-cli
```

To install the latest repository revision instead:

```bash
pipx install git+https://github.com/Sarthak702-droid/VibeGuard.git
```

### pip

```bash
pip install vibegaurd-cli
```

### Install for Development

Clone the repository and set up an editable installation inside a Python virtual environment:

```bash
git clone https://github.com/Sarthak702-droid/VibeGuard.git
cd VibeGuard
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

On Windows PowerShell, activate the environment with `.venv\Scripts\Activate.ps1`.
For a runtime-only editable install, use `python -m pip install -e .`.

---

## 💻 CLI Global Usage & Shortcuts

After installation, VibeGuard is accessible globally using either the full command or its short developer alias:

```bash
vibeguard [COMMAND] [OPTIONS]
# or
vig [COMMAND] [OPTIONS]
```

VibeGuard intentionally does not install a `vg` command because Linux distributions may
already provide that system command. Use `vig` for the short alias.

### Global Options
* `--version` / `-V`: Show the version and exit.
* `--help`: Show command documentation.

---

## 🔧 Command Reference

| Command | Alias | Description | Key Options |
| :--- | :--- | :--- | :--- |
| `init` | `vig init` | Initializes a `.vibeguard/` folder with a template config file. | `-p, --project <path>` |
| `doctor` | `vig doctor` | Diagnoses project health, CLI path issues, and tool chains. | `-p, --project <path>` |
| `scan` | `vig scan` | Detects technology stacks, frameworks, and important files. | `-p, --project <path>` |
| `context` | `vig context` | Creates an AI-readable context report based on project files. | `-g, --goal <str>`, `-p <path>`, `-t <tokens>` |
| `plan` | `vig plan` | Turns a rough concept into a structured implementation plan. | `-g, --goal <str>`, `-p <path>` |
| `prompt` | `vig prompt` | Generates a prompt locally; optionally refines it with NVIDIA GLM-5.2. | `-g, --goal <str>`, `-p <path>`, `-t <tokens>`, `--llm` |
| `pack` | `vig pack` | Packages relevant files into a single context file. | `-g, --goal <str>`, `-p <path>`, `-t <tokens>` |
| `verify` | `vig verify` | Performs automatic checks (lints, test suites, types). | `-p, --project <path>` |
| `diff-explain`| `vig diff-explain` | Summarizes uncommitted code changes in plain English. | `-p, --project <path>` |
| `risks` | `vig risks` | Audits changed files for security issues and logic flags. | `-p, --project <path>` |
| `next-prompt` | `vig next-prompt` | Generates the next best prompt to address risks/failures. | `-p, --project <path>` |
| `all` | `vig all` | Runs the full VibeGuard end-to-end workflow at once. | `-g, --goal <str>`, `-p <path>`, `-t <tokens>` |
| `agents` | `vig agents detect` | Lists, detects, and describes supported coding agents. | `list`, `detect`, `info` |
| `run` | `vig run codex` | Runs a known agent with baseline capture and postflight verification. | `--task`, `--timeout` |
| `exec` | `vig exec -- codex` | Safely passes arguments to a known agent executable. | `--verify/--no-verify` |
| `config` | `vig config show` | Shows, validates, or updates typed project configuration. | `show`, `validate`, `set` |
| `risk` | `vig risk` | Applies deterministic policy checks and risk scoring. | `--json` |
| `secrets` | `vig secrets` | Finds secret-like values while redacting actual credentials. | `--json` |
| `deps` | `vig deps` | Reviews dependency manifests and suspicious package names. | `--json` |
| `explain` | `vig explain` | Generates developer, security, compatibility, and test-impact notes. | — |
| `report` | `vig report` | Generates Markdown, JSON, or SARIF governance output. | `--format` |
| `next` | `vig next` | Creates a corrective prompt from exact failures and risks. | — |
| `ci` | `vig ci generate github` | Generates GitHub/GitLab CI or runs CI-grade checks. | `generate`, `check` |
| `precommit` | `vig precommit install` | Installs a non-destructive local pre-commit hook. | `install` |
| `shell` | `vig shell` | Opens the lightweight VibeGuard workflow shell. | — |

> **Note:** Every command supports a `--no-banner` flag to suppress the terminal startup branding, making automated scripts cleaner.

### Optional NVIDIA GLM-5.2 refinement

Create an NVIDIA API key, store it in the `NVIDIA_API_KEY` environment variable, and
request LLM refinement explicitly:

```bash
# Linux/macOS
export NVIDIA_API_KEY="your-new-rotated-key"
vig prompt -g "add OTP login" --llm
```

```powershell
# Windows PowerShell (current terminal session)
$env:NVIDIA_API_KEY = "your-new-rotated-key"
vig prompt -g "add OTP login" --llm
```

The default model is `z-ai/glm-5.2`. Override it only when using another model exposed by
the same NVIDIA NIM endpoint:

```bash
vig prompt -g "add OTP login" --llm --model z-ai/glm-5.2 --llm-max-tokens 4096
```

Without `--llm`, prompt generation remains fully local. With `--llm`, VibeGuard sends the
generated prompt—which contains project metadata and selected file paths, but not the
selected files' contents—to NVIDIA. Never place API keys in source code, command flags,
`.vibeguard/` outputs, or committed `.env` files.

---

## ⚙️ Core Workflows

### 1. Before Asking AI to Code (Preparing Context)
1. **Initialize** the workspace:
   ```bash
   vig init
   ```
2. **Scan** the stack and frameworks:
   ```bash
   vig scan
   ```
3. Generate **context, plan, and pack files**:
   ```bash
   vig context -g "add OTP login"
   vig plan -g "add OTP login without changing database schemas"
   vig pack -g "add OTP login" -t 8000
   ```
4. Run a supported agent through the guarded wrapper:
   ```bash
   vig run codex --task "add OTP login"
   ```

### 2. After AI Modifies Code (Verifying & Hardening)
1. **Verify** that code compiles and tests pass:
   ```bash
   vig verify
   ```
2. **Review risks** (detects API keys, security breaches, or altered authentication methods):
   ```bash
   vig risks
   ```
3. Get an **explanation of changes**:
   ```bash
   vig diff-explain
   ```
4. Generate the **hardening prompt** to fix any identified failures:
   ```bash
   vig next-prompt
   ```

---

## 📁 Workspace Layout

Project policy lives in `.vibeguard.yml`. Generated runtime state and outputs are
localized within `.vibeguard/`:
```text
.vibeguard/
├── context.md           # Bundled context for AI
├── prompt.md            # Target prompt template
├── task.md              # Detailed implementation plan
├── pack.md              # Token-packed code segments
├── cache/               # Scan results cache
├── sessions/            # Auditable agent-session records
└── reports/             # Post-coding audit reports
    ├── diff_report.md
    ├── risk_report.md
    ├── next_prompt.md
    └── verification_report.md
```

### Recommended Git Configuration
Add VibeGuard's generated reports and caches to your `.gitignore` to keep commits clean:
```gitignore
.vibeguard/cache/
.vibeguard/reports/
```

---

## 🛡️ Security Defaults
VibeGuard is designed to be safe-by-default for enterprise workspaces:
* 🔒 **Scoped operation:** VibeGuard writes its own config/reports and explicitly requested CI or hook files; coding agents remain responsible for source edits.
* 🛡️ **Argument-array execution:** Agent and verification commands use subprocess argument arrays, not `shell=True`.
* 🔐 **Automated Secret Redaction:** Automatically skips sensitive files like `.env`, private keys (`.pem`), and database configuration variables.
* 🚫 **Safe Scans:** Automatically ignores binary assets, node modules, build targets, and large generated directories.
* ⚠️ **Boundary:** V1 observes, records, detects, warns, verifies, and blocks by policy. It does not provide container, namespace, seccomp, VM, network, or credential isolation.

---

## 🗺️ Project Roadmap

### v0.2.0 (Current)
* Canonical `vig` and `vibeguard` commands with legacy `vbg` compatibility.
* Typed configuration, repository baselines and coding-agent adapters.
* Guarded wrapper execution and auditable session records.
* Multi-language verification, risk scoring, secret/dependency checks.
* Markdown, JSON and SARIF reports plus CI/pre-commit generation.

### v0.3.0 (Planned)
* Pull Request audit reporting.
* Framework dependency graphs.
* Dynamic HTML reporting dashboard.

---

## 📦 Package Validation

Run the release checks from an activated development environment:

```bash
python -m pytest
python -m build
python -m twine check dist/*
```

To test the built wheel without changing the development environment:

```bash
python -m venv /tmp/vibeguard-wheel-test
/tmp/vibeguard-wheel-test/bin/python -m pip install dist/*.whl
/tmp/vibeguard-wheel-test/bin/vibeguard --help
/tmp/vibeguard-wheel-test/bin/vig --help
```

On Windows, use the equivalent executables under
`%TEMP%\vibeguard-wheel-test\Scripts\`.

## 🚢 Publishing a Release

Releases are published by `.github/workflows/publish.yml` when a semantic version tag is
pushed. The workflow checks that the tag matches the package version, builds the wheel and
source distribution, validates both with Twine, and publishes with a PyPI API token stored
as a GitHub environment secret.

### Configure the PyPI token

1. Sign in to PyPI and open **Account settings → API tokens → Add API token**.
2. For the existing `vibegaurd-cli` project, create or use a project-scoped token for
   the first upload. Copy it once; PyPI will not show it again.
3. In GitHub, open **Settings → Environments → pypi → Environment secrets**.
4. Create a secret named `PYPI_API_TOKEN` and paste the complete token, including its
   `pypi-` prefix.
5. Keep the token scoped only to `vibegaurd-cli` and rotate it if it was ever exposed.

The workflow references `${{ secrets.PYPI_API_TOKEN }}`; the token itself must never be
written into `publish.yml` or committed to Git.

After updating and committing the version, publish `0.2.0` with:

```bash
git push origin main
git tag v0.2.0
git push origin v0.2.0
```

PyPI does not allow an existing distribution file or version to be overwritten. Never
reuse `v0.1.0`; increment the version and create a new tag for every release.

