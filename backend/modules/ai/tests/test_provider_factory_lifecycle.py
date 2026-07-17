import pytest
import pytest_asyncio

import backend.modules.ai.infrastructure.provider_factory as provider_factory_module
from backend.modules.ai.infrastructure.provider_factory import (
    close_llm_provider,
    get_llm_provider,
    init_llm_provider,
)
from backend.modules.ai.infrastructure.providers.mock_llm_provider import MockLLMProvider
from backend.shared.config.settings import Settings


@pytest_asyncio.fixture(autouse=True)
async def _reset_singleton():
    # The provider is process-global state (mirrors shared/database/*.py's
    # engine/client globals) — reset it around each test so tests don't leak
    # into each other regardless of order.
    yield
    await close_llm_provider()


@pytest.mark.asyncio
async def test_init_then_get_returns_the_same_shared_instance() -> None:
    await init_llm_provider(Settings(ai_provider="mock"))

    provider = get_llm_provider()

    assert isinstance(provider, MockLLMProvider)
    assert get_llm_provider() is provider


@pytest.mark.asyncio
async def test_get_before_init_raises() -> None:
    await close_llm_provider()  # ensure a clean slate

    with pytest.raises(RuntimeError):
        get_llm_provider()


@pytest.mark.asyncio
async def test_close_calls_aclose_when_the_provider_has_one() -> None:
    closed = {"called": False}

    class _FakeProvider:
        async def generate_response(self, prompt):
            raise NotImplementedError

        async def aclose(self) -> None:
            closed["called"] = True

    provider_factory_module._llm_provider = _FakeProvider()

    await close_llm_provider()

    assert closed["called"] is True
    with pytest.raises(RuntimeError):
        get_llm_provider()


@pytest.mark.asyncio
async def test_close_is_a_no_op_when_the_provider_has_no_aclose() -> None:
    await init_llm_provider(Settings(ai_provider="mock"))

    await close_llm_provider()  # MockLLMProvider has no aclose — must not raise
