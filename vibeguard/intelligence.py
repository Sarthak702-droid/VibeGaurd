"""LLM-agnostic intelligence services with a deterministic local fallback."""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from typing import Any

from openai import OpenAI

from vibeguard.core.risk_engine import _redact_secrets_in_line


class IntelligenceError(RuntimeError):
    """An external provider failed without invalidating deterministic results."""


class IntelligenceProvider(ABC):
    @abstractmethod
    def health_check(self) -> bool: ...

    @abstractmethod
    def generate_plan(self, request: str, context: str) -> dict[str, Any]: ...

    @abstractmethod
    def analyze_diff(self, diff: str, context: str) -> dict[str, Any]: ...

    @abstractmethod
    def explain_risks(self, findings: list[dict[str, Any]], context: str) -> str: ...

    @abstractmethod
    def generate_next_prompt(self, findings: list[dict[str, Any]], plan: str) -> str: ...


class DeterministicProvider(IntelligenceProvider):
    def health_check(self) -> bool:
        return True

    def generate_plan(self, request: str, context: str) -> dict[str, Any]:
        return {"objective": request, "steps": ["Inspect relevant code", "Implement scoped change", "Add tests", "Verify"]}

    def analyze_diff(self, diff: str, context: str) -> dict[str, Any]:
        return {"summary": "Local deterministic analysis", "changed_lines": len(diff.splitlines())}

    def explain_risks(self, findings: list[dict[str, Any]], context: str) -> str:
        return "\n".join(f"- {item.get('severity', 'INFO')}: {item.get('message', 'Finding')}" for item in findings)

    def generate_next_prompt(self, findings: list[dict[str, Any]], plan: str) -> str:
        failures = "\n".join(f"- {item.get('message', 'Resolve finding')}" for item in findings) or "- Re-run verification"
        return f"Correct only these unresolved findings:\n{failures}\n\nPreserve unrelated files and run relevant tests."


class GLMProvider(IntelligenceProvider):
    def __init__(
        self,
        *,
        model: str = "z-ai/glm-5.2",
        api_key: str | None = None,
        base_url: str = "https://integrate.api.nvidia.com/v1",
        timeout: float = 60,
    ) -> None:
        key = api_key or os.getenv("NVIDIA_API_KEY")
        if not key:
            raise IntelligenceError("NVIDIA_API_KEY is not configured.")
        self.model = model
        self.client = OpenAI(base_url=base_url, api_key=key, timeout=timeout, max_retries=2)

    def health_check(self) -> bool:
        try:
            self._request("Return JSON: {\"ok\": true}")
        except IntelligenceError:
            return False
        return True

    def generate_plan(self, request: str, context: str) -> dict[str, Any]:
        return self._request(f"Create a scoped implementation plan as JSON.\nRequest: {request}\nContext:\n{context}")

    def analyze_diff(self, diff: str, context: str) -> dict[str, Any]:
        return self._request(f"Explain this already-extracted diff as JSON.\nContext:\n{context}\nDiff:\n{diff}")

    def explain_risks(self, findings: list[dict[str, Any]], context: str) -> str:
        result = self._request(f"Explain deterministic risks as JSON with an explanation field.\n{json.dumps(findings)}\n{context}")
        return str(result.get("explanation", result))

    def generate_next_prompt(self, findings: list[dict[str, Any]], plan: str) -> str:
        result = self._request(f"Create a corrective coding-agent prompt as JSON with a prompt field.\n{json.dumps(findings)}\n{plan}")
        return str(result.get("prompt", result))

    def _request(self, prompt: str) -> dict[str, Any]:
        redacted = "\n".join(_redact_secrets_in_line(line) for line in prompt.splitlines())
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Return valid JSON only. Never reveal secrets."},
                    {"role": "user", "content": redacted},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
            )
            content = response.choices[0].message.content or "{}"
            value = json.loads(content)
            if not isinstance(value, dict):
                raise ValueError("response is not an object")
            return value
        except Exception as exc:
            raise IntelligenceError(f"GLM request failed ({type(exc).__name__}).") from exc


def get_provider(*, provider: str, model: str, local_only: bool) -> IntelligenceProvider:
    if local_only or provider in {"local", "deterministic", "none"}:
        return DeterministicProvider()
    if provider == "glm":
        return GLMProvider(model=model)
    raise IntelligenceError(f"Unsupported intelligence provider: {provider}")
