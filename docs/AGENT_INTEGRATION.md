# Coding-Agent Integration Guide

The validated V1 adapter scope is OpenAI Codex and Antigravity CLI. Claude Code,
Gemini CLI, Aider, and Cursor CLI are intentionally deferred until a later
release can test their installation, authentication, flags, and terminal behavior.

```bash
vig agents detect
vig agents info codex
vig run codex --task "Add secure authentication"
vig exec -- codex
```

`vig run` captures a baseline, launches the resolved executable, preserves its
terminal streams, forwards interruption, records exit/session metadata, compares
file hashes, and runs postflight verification. `vig exec` accepts only a known
adapter name; it is not a general shell escape.

Adapters must declare vendor-specific non-interactive arguments. Do not assume
that one provider's flags work for another. Tests should use a mock executable
and must not require a real agent installation.

Agent CLIs execute with the user's operating-system permissions. VibeGuard V1
does not restrict their filesystem or network access.
