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
        system_parts = [f"You are a helpful assistant for the category: {prompt.category}."]
        if prompt.user_profile:
            system_parts.append(f"User profile: {prompt.user_profile}")
        if prompt.system_context:
            system_parts.append(prompt.system_context)

        messages = [{"role": "system", "content": "\n".join(system_parts)}]
        messages.extend({"role": turn.role, "content": turn.content} for turn in prompt.conversation_history)
        messages.append({"role": "user", "content": prompt.question})
        return messages
