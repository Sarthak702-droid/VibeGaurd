# Contributing to VibeGuard

Use Python 3.11 or newer, create a virtual environment, and install development
dependencies with `pip install -e ".[dev]"`. Keep deterministic safety features
usable without an external LLM. Add unit tests for adapters, configuration,
scanners and serializers; use mock agents/providers for integration tests.

Before opening a pull request, run:

```bash
pytest -q
ruff check .
python -m build
vig --help
```

Never commit credentials or test against a real paid provider in the default
test suite.
