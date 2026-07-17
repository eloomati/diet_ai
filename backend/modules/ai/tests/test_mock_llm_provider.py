import pytest

from backend.modules.ai.domain import Prompt
from backend.modules.ai.infrastructure.providers.mock_llm_provider import MockLLMProvider


@pytest.mark.asyncio
async def test_mock_llm_provider_returns_deterministic_response() -> None:
    provider = MockLLMProvider()

    response = await provider.generate_response(
        Prompt(question="What should I eat for breakfast?", category="BREAKFAST")
    )

    assert response.model == "mock"
    assert "BREAKFAST" in response.content
    assert response.tokens > 0
