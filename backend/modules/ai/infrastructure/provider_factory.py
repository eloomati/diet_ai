from backend.modules.ai.domain import LLMProvider
from backend.modules.ai.infrastructure.anthropic.claude_provider import ClaudeProvider
from backend.modules.ai.infrastructure.ollama.ollama_provider import OllamaProvider
from backend.modules.ai.infrastructure.providers.mock_llm_provider import MockLLMProvider
from backend.shared.config.settings import Settings


def build_llm_provider(settings: Settings) -> LLMProvider:
    if settings.ai_provider == "mock":
        return MockLLMProvider()

    if settings.ai_provider == "claude":
        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY must be set when AI_PROVIDER=claude.")
        return ClaudeProvider(api_key=settings.anthropic_api_key, model=settings.anthropic_model)

    if settings.ai_provider == "ollama":
        return OllamaProvider(base_url=settings.ollama_base_url, model=settings.ollama_model)

    raise ValueError(f"Unknown AI_PROVIDER: {settings.ai_provider!r} (expected mock|claude|ollama).")
