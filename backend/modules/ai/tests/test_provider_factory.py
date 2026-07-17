import pytest

from backend.modules.ai.infrastructure.anthropic.claude_provider import ClaudeProvider
from backend.modules.ai.infrastructure.ollama.ollama_provider import OllamaProvider
from backend.modules.ai.infrastructure.provider_factory import build_llm_provider
from backend.modules.ai.infrastructure.providers.mock_llm_provider import MockLLMProvider
from backend.shared.config.settings import Settings


def test_build_llm_provider_mock() -> None:
    settings = Settings(ai_provider="mock")

    assert isinstance(build_llm_provider(settings), MockLLMProvider)


def test_build_llm_provider_claude_requires_api_key() -> None:
    settings = Settings(ai_provider="claude", anthropic_api_key=None)

    with pytest.raises(RuntimeError):
        build_llm_provider(settings)


def test_build_llm_provider_claude_with_key() -> None:
    settings = Settings(ai_provider="claude", anthropic_api_key="sk-test", anthropic_model="claude-opus-4-8")

    assert isinstance(build_llm_provider(settings), ClaudeProvider)


def test_build_llm_provider_ollama() -> None:
    settings = Settings(
        ai_provider="ollama", ollama_base_url="http://localhost:11434", ollama_model="llama3.2:1b"
    )

    assert isinstance(build_llm_provider(settings), OllamaProvider)


def test_build_llm_provider_unknown_raises() -> None:
    settings = Settings(ai_provider="bogus")

    with pytest.raises(ValueError):
        build_llm_provider(settings)
