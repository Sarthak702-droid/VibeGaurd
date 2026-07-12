# Installing VibeGuard CLI

VibeGuard is distributed as the Python package `vibegaurd-cli` and exposes these
terminal commands:

```text
vig          # Primary command
vibeguard    # Full alias
vbg          # Legacy compatibility alias
```

The distribution spelling remains `vibegaurd-cli` because the correctly spelled
`vibeguard` and `vibeguard-cli` names are owned by unrelated PyPI projects. The
product name, Python import and primary CLI remain correctly spelled as
VibeGuard, `vibeguard` and `vig`.

## Install the latest GitHub version

Until VibeGuard 0.2.0 is published to PyPI, install the latest release directly
from the GitHub repository.

### macOS and Linux

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
python3 -m pipx install git+https://github.com/Sarthak702-droid/VibeGuard.git
```

Restart the terminal after `ensurepath`, then verify the installation:

```bash
vig --version
vig --help
vig doctor
```

### Windows PowerShell

```powershell
py -m pip install --user pipx
py -m pipx ensurepath
py -m pipx install git+https://github.com/Sarthak702-droid/VibeGuard.git
```

Restart PowerShell, then verify:

```powershell
vig --version
vig --help
vig doctor
```

### Windows Command Prompt

```cmd
py -m pip install --user pipx && py -m pipx ensurepath && py -m pipx install git+https://github.com/Sarthak702-droid/VibeGuard.git
```

Restart Command Prompt, then verify:

```cmd
vig --version
vig --help
vig doctor
```

## Install from PyPI

After version 0.2.0 is published, the recommended isolated installation on
macOS, Linux and Windows will be:

```bash
pipx install vibegaurd-cli
```

The standard pip alternative is:

```bash
python -m pip install vibegaurd-cli
```

Verify either installation with:

```bash
vig --version
vig --help
```

## Upgrade

For a PyPI installation:

```bash
pipx upgrade vibegaurd-cli
```

For a GitHub installation:

```bash
pipx reinstall vibegaurd-cli
```

## Uninstall

```bash
pipx uninstall vibegaurd-cli
```

## First VibeGuard workflow

Run these commands inside a Git repository that you want to inspect:

```bash
cd /path/to/your-project

vig init
vig scan
vig plan "Add secure JWT authentication"
vig context --task "Add secure JWT authentication"
vig run codex --task "Add secure JWT authentication"
vig verify --full
vig secrets
vig deps
vig risk
vig explain
vig report
vig next
```

The currently validated coding-agent adapters are Codex and Antigravity:

```bash
vig agents list
vig run codex --task "Review this project"
vig run antigravity --task "Review this project"
```

## Planned one-line installers

To provide an installation page like Antigravity CLI, VibeGuard will need these
three reviewed installer scripts in the repository:

```text
scripts/install.sh
scripts/install.ps1
scripts/install.cmd
```

After those scripts are implemented and security-reviewed, the intended commands
will be:

### Planned macOS and Linux command

```bash
curl -fsSL https://raw.githubusercontent.com/Sarthak702-droid/VibeGuard/main/scripts/install.sh | sh
```

### Planned Windows PowerShell command

```powershell
irm https://raw.githubusercontent.com/Sarthak702-droid/VibeGuard/main/scripts/install.ps1 | iex
```

### Planned Windows Command Prompt command

```cmd
curl -fsSL https://raw.githubusercontent.com/Sarthak702-droid/VibeGuard/main/scripts/install.cmd -o install.cmd && install.cmd && del install.cmd
```

> These one-line commands are documentation of the planned experience. Do not
> run or publish them until the referenced scripts actually exist and have been
> reviewed. Piping remote scripts directly into a shell should only be offered
> from versioned, integrity-controlled release URLs.
