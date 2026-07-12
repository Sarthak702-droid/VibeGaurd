# GLM and Intelligence Configuration

Local deterministic mode is the default:

```yaml
intelligence:
  provider: glm
  model: z-ai/glm-5.2
  local_only: true
```

To opt into the NVIDIA-hosted GLM adapter, set `local_only: false` and provide
`NVIDIA_API_KEY` through the environment. Never store credentials in
`.vibeguard.yml`.

Environment overrides include:

- `VIBEGUARD_INTELLIGENCE_PROVIDER`
- `VIBEGUARD_INTELLIGENCE_MODEL`
- `VIBEGUARD_LOCAL_ONLY`
- `VIBEGUARD_DEFAULT_AGENT`

All provider calls go through `IntelligenceProvider`. Prompts are redacted before
external transmission, calls use timeouts/retries, structured JSON is validated,
and provider errors surface as non-fatal intelligence errors. Deterministic test,
security and policy outcomes are never delegated to the model.
