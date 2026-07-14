# Publishing `vibegaurd-rust-client`

The PyPI distribution name is `vibegaurd-rust-client`, intentionally separate
from the occupied `vibeguard` namespace. Name availability can change until the
first successful upload, so validate it immediately before publishing.

```bash
cd python-client
python -m build
python -m twine check dist/*
python -m twine upload dist/*
```

This package does not bundle a Rust executable. Users install a matching
VibeGuard binary separately, keep it on `PATH`, or point to it through
`VIBEGAURD_BINARY`.
