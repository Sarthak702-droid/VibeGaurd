from __future__ import annotations

from types import SimpleNamespace

import pytest

from vibeguard.llm import LLMConfigurationError, enhance_coding_prompt


def test_llm_requires_environment_key(monkeypatch) -> None:
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)

    with pytest.raises(LLMConfigurationError, match="NVIDIA_API_KEY"):
        enhance_coding_prompt("Improve this prompt")


def test_llm_collects_streamed_content_without_exposing_key(monkeypatch) -> None:
    monkeypatch.setenv("NVIDIA_API_KEY", "test-key-not-real")
    captured = {}

    class FakeCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            return [
                SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="# Improved"))]),
                SimpleNamespace(choices=[]),
                SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="\nPrompt"))]),
            ]

    class FakeClient:
        def __init__(self, *, base_url, api_key):
            captured["base_url"] = base_url
            captured["api_key"] = api_key
            self.chat = SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setattr("vibeguard.llm.OpenAI", FakeClient)

    result = enhance_coding_prompt("Original", max_tokens=123)

    assert result == "# Improved\nPrompt\n"
    assert captured["model"] == "z-ai/glm-5.2"
    assert captured["max_tokens"] == 123
    assert captured["stream"] is True
    assert captured["messages"][1]["content"] == "Original"
