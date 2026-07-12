# Security Policy

Report vulnerabilities privately through the repository's GitHub security
advisory feature. Do not include live credentials in an issue.

VibeGuard V1 is a guarded execution and verification layer, not an OS-level
sandbox. It records baselines, runs known agent executables without `shell=True`,
redacts likely secrets, applies deterministic policies, and can block on findings.
It does not isolate the filesystem, network, process namespace, resources, or
credentials. Run third-party coding agents only with permissions you are willing
to grant them.

External intelligence is opt-in. Repository context must be reviewed before it is
sent to a provider, and secret-like values are redacted first.
