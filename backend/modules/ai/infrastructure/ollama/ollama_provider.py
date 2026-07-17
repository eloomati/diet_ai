
import time

import httpx

from backend.modules.ai.domain import AIResponse, LLMProvider, Prompt


class OllamaProvider(LLMProvider):
    """Talks to a local/self-hosted Ollama server over its HTTP API (no official SDK)."""

    def __init__(
        self,
        base_url: str,
        model: str,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._model = model
        self._client = client or httpx.AsyncClient(base_url=base_url, timeout=60.0)

    async def generate_response(self, prompt: Prompt) -> AIResponse:
        started_at = time.monotonic()
        response = await self._client.post(
            "/api/chat",
            json={
                "model": self._model,
                "messages": self._build_messages(prompt),
                "stream": False,
            },
        )
        response.raise_for_status()
        execution_time = time.monotonic() - started_at

        body = response.json()
        content = body.get("message", {}).get("content", "")

        return AIResponse(
            content=content,
            model=body.get("model", self._model),
            tokens=body.get("eval_count", 0),
            execution_time=execution_time,
        )

    def _build_messages(self, prompt: Prompt) -> list[dict[str, str]]:
        messages = [{"role": "system", "content": prompt.system_prompt}]
        messages.extend({"role": turn.role, "content": turn.content} for turn in prompt.conversation_history)
        messages.append({"role": "user", "content": prompt.question})
        return messages

    async def aclose(self) -> None:
        await self._client.aclose()
