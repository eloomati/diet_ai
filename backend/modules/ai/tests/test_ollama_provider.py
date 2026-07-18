import pytest

from backend.modules.ai.domain import Prompt
from backend.modules.ai.infrastructure.ollama.ollama_provider import OllamaProvider

_DIET_PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "days": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "day_number": {"type": "integer"},
                    "meals": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "calories": {"type": "number"},
                                "protein": {"type": "number"},
                                "carbohydrates": {"type": "number"},
                                "fat": {"type": "number"},
                            },
                            "required": ["name", "calories", "protein", "carbohydrates", "fat"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["day_number", "meals"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["days"],
    "additionalProperties": False,
}


class _FakeHttpResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict:
        return self._payload


class _FakeHttpClient:
    def __init__(self, payload: dict) -> None:
        self._payload = payload
        self.last_url: str | None = None
        self.last_json: dict = {}
        self.closed = False

    async def post(self, url: str, json: dict):
        self.last_url = url
        self.last_json = json
        return _FakeHttpResponse(self._payload)

    async def aclose(self) -> None:
        self.closed = True


class _SequencedHttpClient:
    """Returns a different payload on each successive call — for retry tests."""

    def __init__(self, payloads: list[dict]) -> None:
        self._payloads = payloads
        self.call_count = 0

    async def post(self, url: str, json: dict):
        response = _FakeHttpResponse(self._payloads[self.call_count])
        self.call_count += 1
        return response


@pytest.mark.asyncio
async def test_ollama_provider_maps_response_to_ai_response() -> None:
    fake_client = _FakeHttpClient(
        {"model": "llama3.2:1b", "message": {"content": "Try oatmeal."}, "eval_count": 8}
    )
    provider = OllamaProvider(base_url="http://localhost:11434", model="llama3.2:1b", client=fake_client)

    response = await provider.generate_response(
        Prompt(question="What should I eat?", categories=("BREAKFAST",))
    )

    assert response.content == "Try oatmeal."
    assert response.model == "llama3.2:1b"
    assert response.tokens == 8
    assert fake_client.last_url == "/api/chat"
    assert fake_client.last_json["model"] == "llama3.2:1b"
    assert fake_client.last_json["messages"][-1] == {"role": "user", "content": "What should I eat?"}


@pytest.mark.asyncio
async def test_ollama_provider_sends_system_prompt_as_first_message() -> None:
    fake_client = _FakeHttpClient(
        {"model": "llama3.2:1b", "message": {"content": "..."}, "eval_count": 1}
    )
    provider = OllamaProvider(base_url="http://localhost:11434", model="llama3.2:1b", client=fake_client)

    await provider.generate_response(
        Prompt(
            question="What should I eat?",
            categories=("BREAKFAST",),
            system_prompt="You are a nutrition assistant. Category: BREAKFAST.",
        )
    )

    assert fake_client.last_json["messages"][0] == {
        "role": "system",
        "content": "You are a nutrition assistant. Category: BREAKFAST.",
    }


_VALID_PLAN = {
    "message": {
        "content": (
            '{"days": [{"day_number": 1, "meals": [{"name": "Oatmeal", "calories": 400, '
            '"protein": 20, "carbohydrates": 60, "fat": 10}]}]}'
        )
    }
}


@pytest.mark.asyncio
async def test_ollama_provider_generate_structured_response_parses_and_validates() -> None:
    fake_client = _FakeHttpClient(_VALID_PLAN)
    provider = OllamaProvider(base_url="http://localhost:11434", model="llama3.2:1b", client=fake_client)

    result = await provider.generate_structured_response(
        Prompt(question="Generate a 1-day diet plan.", categories=("DIET",)), _DIET_PLAN_SCHEMA
    )

    assert result["days"][0]["day_number"] == 1
    assert result["days"][0]["meals"][0]["name"] == "Oatmeal"
    assert fake_client.last_json["format"] == "json"


@pytest.mark.asyncio
async def test_ollama_provider_retries_once_on_invalid_json_then_succeeds() -> None:
    fake_client = _SequencedHttpClient(
        [{"message": {"content": "not valid json"}}, _VALID_PLAN]
    )
    provider = OllamaProvider(base_url="http://localhost:11434", model="llama3.2:1b", client=fake_client)

    result = await provider.generate_structured_response(
        Prompt(question="Generate a 1-day diet plan.", categories=("DIET",)), _DIET_PLAN_SCHEMA
    )

    assert fake_client.call_count == 2
    assert result["days"][0]["meals"][0]["name"] == "Oatmeal"


@pytest.mark.asyncio
async def test_ollama_provider_raises_after_retry_also_fails() -> None:
    fake_client = _SequencedHttpClient(
        [{"message": {"content": "not json"}}, {"message": {"content": "still not json"}}]
    )
    provider = OllamaProvider(base_url="http://localhost:11434", model="llama3.2:1b", client=fake_client)

    with pytest.raises(RuntimeError, match="did not return valid structured JSON"):
        await provider.generate_structured_response(
            Prompt(question="Generate a 1-day diet plan.", categories=("DIET",)), _DIET_PLAN_SCHEMA
        )

    assert fake_client.call_count == 2


@pytest.mark.asyncio
async def test_ollama_provider_aclose_closes_underlying_client() -> None:
    fake_client = _FakeHttpClient({"model": "llama3.2:1b", "message": {"content": "..."}, "eval_count": 1})
    provider = OllamaProvider(base_url="http://localhost:11434", model="llama3.2:1b", client=fake_client)

    await provider.aclose()

    assert fake_client.closed is True
