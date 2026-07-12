# VibeGuard Architecture

VibeGuard is a guarded execution and verification layer around vendor-specific
coding-agent CLIs.

```text
CLI
 ├─ typed config and policy
 ├─ repository scanner/context/planner
 ├─ coding-agent registry and runner
 │   └─ baseline → subprocess → snapshot comparison → session record
 ├─ verification and deterministic security
 ├─ optional intelligence provider
 └─ terminal/Markdown/JSON/SARIF reports
```

The CLI handlers coordinate services; scanning, snapshots, agents, security,
intelligence and report serialization live in separate modules. Agent commands
are constructed as argument arrays. Unknown executables are rejected by `vig
exec`. Verification uses an explicit command allowlist and never uses
`shell=True`.

The deterministic layer remains authoritative for test results, secrets,
protected paths, change size and policy decisions. GLM can plan, correlate and
explain, but provider failure never changes a failed check into a pass.

Generated state is stored below `.vibeguard/`; project policy is stored in
`.vibeguard.yml`. Baselines hash eligible repository files so pre-existing
changes can be separated from files changed after an agent session starts.

## Extension points

- Add an agent by registering an `AgentAdapter` with its exact executable and
  task arguments.
- Add an intelligence provider by implementing `IntelligenceProvider`.
- Add deterministic findings without depending on an LLM.
- Add report formats from the normalized `GovernanceReport` model.
