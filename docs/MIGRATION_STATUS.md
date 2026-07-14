# Rust Migration Status

The Cargo workspace is the primary product and produces the `vibeguard` and
`vbg` binaries. The legacy Python source and tests have been copied to
`legacy-python/` for parity reference; they are not referenced by the Rust
workspace, CI, or release workflow.

Implemented Rust domains:

- CLI routing, stable exit mapping, doctor, configuration, cache, auth
  diagnostics, CI generation, pre-commit installation, and agent adapters.
- Safe local scanning and remote bare-Git ingestion with credential-free cache
  keys, prompt suppression, SSH batch mode, and transport restrictions.
- Offline context packing, planning, prompt generation, deterministic diff risk
  rules, secret scanning/redaction, dependency checks, and direct-argument
  verification.
- Versioned Markdown, JSON, and SARIF reporting.

Intentional migration differences:

- Project configuration is `.vibeguard.toml`; legacy YAML is retained only in
  the reference implementation.
- `vig` is removed. `vbg` remains. `vg` is never created.
- The optional NVIDIA Python/OpenAI feature is replaced with a provider trait;
  core commands stay offline.

Current validation is recorded in the repository's migration handoff. The
release workflow builds Rust artifacts; the obsolete Python/PyPI workflow was
removed.
