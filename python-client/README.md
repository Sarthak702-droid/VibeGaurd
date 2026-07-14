# VIBEGAURD Python client

`vibegaurd-rust-client` is a dependency-free Python adapter for the Rust
VibeGuard backend. It does not implement scanning itself and does not need a
Python server. The installed command is exactly `VIBEGAURD`.

```bash
pip install vibegaurd-rust-client
VIBEGAURD --backend /path/to/vibeguard scan-local ../repository
VIBEGAURD scan-github https://github.com/owner/repository.git --ref main
```

The Python API uses direct argument arrays and accepts only public HTTPS GitHub
URLs for `scan_public_github`. For a repository that the user already cloned or
pulled, use `scan_local`; no network access is needed.

```python
from vibegaurd_client import VibeGaurdClient

client = VibeGaurdClient("/path/to/vibeguard")
result = client.scan_local("../already-cloned-repository")
print(result.stdout)
```

Set `VIBEGAURD_BINARY` when the Rust backend is not on `PATH`.
