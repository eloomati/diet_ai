import pytest

from backend.modules.ai.domain import Prompt
from backend.modules.ai.infrastructure.providers.mock_llm_provider import MockLLMProvider


@pytest.mark.asyncio
async def test_mock_llm_provider_returns_deterministic_response() -> None:
    provider = MockLLMProvider()

    response = await provider.generate_response(
        Prompt(question="What should I eat for breakfast?", categories=("BREAKFAST",))
    )

    assert response.model == "mock"
    assert "BREAKFAST" in response.content
    assert response.tokens > 0


@pytest.mark.asyncio
async def test_mock_llm_provider_generates_matching_day_count() -> None:
    provider = MockLLMProvider()

    result = await provider.generate_structured_response(
        Prompt(question="Generate a 3-day diet plan for this user.", categories=("DIET",)), schema={}
    )

    assert len(result["days"]) == 3
    assert [day["day_number"] for day in result["days"]] == [1, 2, 3]
    assert result["days"][0]["meals"][0]["name"] == "Mock meal"
