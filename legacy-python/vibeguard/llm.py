"""Optional NVIDIA-hosted LLM enhancement for generated coding prompts."""

from __future__ import annotations

import os

from openai import OpenAI


NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
DEFAULT_NVIDIA_MODEL = "z-ai/glm-5.2"
DEFAULT_MAX_TOKENS = 4096


class LLMConfigurationError(RuntimeError):
    """Raised when the optional LLM integration is not configured."""


class LLMRequestError(RuntimeError):
    """Raised when the NVIDIA model does not return usable content."""


def enhance_coding_prompt(
    prompt: str,
    *,
    model: str = DEFAULT_NVIDIA_MODEL,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> str:
    """Refine a locally generated coding prompt with NVIDIA's OpenAI-compatible API."""
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        raise LLMConfigurationError(
            "NVIDIA_API_KEY is not configured. Set it in your environment before using --llm."
        )
    if max_tokens < 1:
        raise LLMConfigurationError("LLM max tokens must be greater than zero.")

    client = OpenAI(base_url=NVIDIA_BASE_URL, api_key=api_key)
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You refine implementation prompts for coding agents. Return only the improved "
                        "Markdown prompt. Preserve all safety, scope, testing, secret-handling, and "
                        "do-not-touch rules. Do not claim to have inspected files whose contents were "
                        "not provided."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=1,
            top_p=1,
            max_tokens=max_tokens,
            seed=42,
            stream=True,
        )
        parts: list[str] = []
        for chunk in completion:
            choices = getattr(chunk, "choices", None)
            if not choices:
                continue
            delta = getattr(choices[0], "delta", None)
            content = getattr(delta, "content", None) if delta is not None else None
            if content:
                parts.append(content)
    except Exception as exc:
        raise LLMRequestError(f"NVIDIA LLM request failed ({type(exc).__name__}).") from exc

    result = "".join(parts).strip()
    if not result:
        raise LLMRequestError("NVIDIA LLM returned no prompt content.")
    return result + "\n"
