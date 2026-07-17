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


# Built once at app startup and reused across requests — same lifecycle shape as
# shared/database/postgres.py's engine and mongo.py's client. Without this,
# the FastAPI dependency would call build_llm_provider() per request, opening a
# fresh HTTP client (and connection pool) on every single chat message with
# nothing ever closing it.
_llm_provider: LLMProvider | None = None


async def init_llm_provider(settings: Settings) -> None:
    global _llm_provider
    _llm_provider = build_llm_provider(settings)


async def close_llm_provider() -> None:
    global _llm_provider
    if _llm_provider is not None:
        aclose = getattr(_llm_provider, "aclose", None)
        if aclose is not None:
            await aclose()
    _llm_provider = None


def get_llm_provider() -> LLMProvider:
    if _llm_provider is None:
        raise RuntimeError("LLM provider not initialized — call init_llm_provider() during app startup.")
    return _llm_provider
