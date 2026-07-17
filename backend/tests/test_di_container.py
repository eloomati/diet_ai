import pytest

from backend.shared.providers import create_di_container


def test_di_container_registers_ai_provider():
    container = create_di_container(use_mock_ai=True)
    ai_provider = container.get("ai_provider")

    assert ai_provider is not None


def test_di_container_raises_on_missing_service():
    container = create_di_container(use_mock_ai=True)

    with pytest.raises(ValueError, match="Service 'unknown' not registered"):
        container.get("unknown")


@pytest.mark.asyncio
async def test_mock_ai_provider():
    from backend.shared.providers import MockLLMProvider

    provider = MockLLMProvider()
    response = await provider.generate_response("Hello AI")

    assert isinstance(response, str)
    assert "Mock AI response" in response