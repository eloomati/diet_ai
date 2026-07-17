import pytest

from backend.modules.ai.domain import Prompt
from backend.modules.ai.infrastructure.ollama.ollama_provider import OllamaProvider


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

    async def post(self, url: str, json: dict):
        self.last_url = url
        self.last_json = json
        return _FakeHttpResponse(self._payload)


@pytest.mark.asyncio
async def test_ollama_provider_maps_response_to_ai_response() -> None:
    fake_client = _FakeHttpClient(
        {"model": "llama3.2:1b", "message": {"content": "Try oatmeal."}, "eval_count": 8}
    )
    provider = OllamaProvider(base_url="http://localhost:11434", model="llama3.2:1b", client=fake_client)

    response = await provider.generate_response(
        Prompt(question="What should I eat?", category="BREAKFAST")
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
            category="BREAKFAST",
            system_prompt="You are a nutrition assistant. Category: BREAKFAST.",
        )
    )

    assert fake_client.last_json["messages"][0] == {
        "role": "system",
        "content": "You are a nutrition assistant. Category: BREAKFAST.",
    }
