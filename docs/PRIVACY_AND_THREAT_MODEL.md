# Privacy and Threat Model

## Protected assets

- Repository source, credentials and private configuration
- Integrity of existing user changes and Git history
- Terminal/process control and audit records
- Accuracy of verification and policy decisions

## Threats addressed in V1

- Secret-like values included in source or context
- Unknown executable invocation through the wrapper
- Unsafe shell construction in VibeGuard-owned subprocesses
- Protected-path, auth, CI, migration, dependency and large-diff changes
- Agent changes incorrectly mixed with a pre-session baseline
- External LLM failure or unavailability

## Residual threats

An installed coding agent may read/write any resource permitted to the user,
access the network, spawn child processes, or consume credentials from its
environment. Pattern scanners can have false positives and false negatives.
Hash baselines attribute file state changes, not human intent. A compromised
verification tool can execute arbitrary code during tests/builds.

Use a container or VM and restricted credentials when stronger isolation is
required. Review context before enabling an external provider. Rotate any secret
reported by VibeGuard even when it is removed from the working tree, because Git
history and logs may retain it.
