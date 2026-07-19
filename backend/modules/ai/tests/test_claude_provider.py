import pytest

from backend.modules.ai.domain import Prompt, PromptTurn
from backend.modules.ai.infrastructure.anthropic.claude_provider import ClaudeProvider


class _FakeTextBlock:
    def __init__(self, text: str) -> None:
        self.type = "text"
        self.text = text


class _FakeUsage:
    def __init__(self, output_tokens: int) -> None:
        self.output_tokens = output_tokens


class _FakeMessage:
    def __init__(self, text: str, model: str, output_tokens: int) -> None:
        self.content = [_FakeTextBlock(text)]
        self.model = model
        self.usage = _FakeUsage(output_tokens)


class _FakeMessagesResource:
    def __init__(self, response: _FakeMessage) -> None:
        self._response = response
        self.last_kwargs: dict = {}

    async def create(self, **kwargs):
        self.last_kwargs = kwargs
        return self._response


class _FakeAnthropicClient:
    def __init__(self, response: _FakeMessage) -> None:
        self.messages = _FakeMessagesResource(response)
        self.closed = False

    async def close(self) -> None:
        self.closed = True


@pytest.mark.asyncio
async def test_claude_provider_maps_response_to_ai_response() -> None:
    fake_client = _FakeAnthropicClient(
        _FakeMessage(text="Try oatmeal.", model="claude-opus-4-8", output_tokens=12)
    )
    provider = ClaudeProvider(api_key="test-key", model="claude-opus-4-8", client=fake_client)

    response = await provider.generate_response(
        Prompt(question="What should I eat?", categories=("BREAKFAST",))
    )

    assert response.content == "Try oatmeal."
    assert response.model == "claude-opus-4-8"
    assert response.tokens == 12


@pytest.mark.asyncio
async def test_claude_provider_builds_messages_from_history() -> None:
    fake_client = _FakeAnthropicClient(
        _FakeMessage(text="Try oatmeal again.", model="claude-opus-4-8", output_tokens=5)
    )
    provider = ClaudeProvider(api_key="test-key", client=fake_client)

    prompt = Prompt(
        question="And tomorrow?",
        categories=("BREAKFAST",),
        system_prompt="You are a nutrition assistant. Category: BREAKFAST.",
        conversation_history=(
            PromptTurn(role="user", content="Hi"),
            PromptTurn(role="assistant", content="Hello, how can I help?"),
        ),
    )
    await provider.generate_response(prompt)

    sent = fake_client.messages.last_kwargs
    assert sent["messages"] == [
        {"role": "user", "content": "Hi"},
        {"role": "assistant", "content": "Hello, how can I help?"},
        {"role": "user", "content": "And tomorrow?"},
    ]
    assert sent["system"] == "You are a nutrition assistant. Category: BREAKFAST."


_DIET_PLAN_SCHEMA = {
    "type": "object",
    "properties": {"days": {"type": "array", "items": {"type": "object", "properties": {}}}},
    "required": ["days"],
    "additionalProperties": False,
}


@pytest.mark.asyncio
async def test_claude_provider_generate_structured_response_parses_json() -> None:
    fake_client = _FakeAnthropicClient(
        _FakeMessage(text='{"days": [{"day_number": 1, "meals": []}]}', model="claude-opus-4-8", output_tokens=10)
    )
    provider = ClaudeProvider(api_key="test-key", client=fake_client)

    result = await provider.generate_structured_response(
        Prompt(question="Generate a 1-day diet plan.", categories=("DIET",)), _DIET_PLAN_SCHEMA
    )

    assert result == {"days": [{"day_number": 1, "meals": []}]}


@pytest.mark.asyncio
async def test_claude_provider_generate_structured_response_sends_output_config() -> None:
    fake_client = _FakeAnthropicClient(
        _FakeMessage(text='{"days": []}', model="claude-opus-4-8", output_tokens=1)
    )
    provider = ClaudeProvider(api_key="test-key", client=fake_client)

    await provider.generate_structured_response(
        Prompt(question="Generate a plan.", categories=("DIET",)), _DIET_PLAN_SCHEMA
    )

    sent = fake_client.messages.last_kwargs
    assert sent["output_config"] == {"format": {"type": "json_schema", "schema": _DIET_PLAN_SCHEMA}}


@pytest.mark.asyncio
async def test_claude_provider_aclose_closes_underlying_client() -> None:
    fake_client = _FakeAnthropicClient(_FakeMessage(text="...", model="claude-opus-4-8", output_tokens=1))
    provider = ClaudeProvider(api_key="test-key", client=fake_client)

    await provider.aclose()

    assert fake_client.closed is True
