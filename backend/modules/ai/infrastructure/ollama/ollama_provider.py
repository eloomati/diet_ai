
import json
import time

import httpx
from pydantic import ValidationError

from backend.modules.ai.domain import AIResponse, LLMProvider, Prompt
from backend.shared.utils import build_example_from_schema, build_model_from_schema


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

    async def generate_structured_response(self, prompt: Prompt, schema: dict) -> dict:
        # Ollama's "format": "json" only guarantees syntactically valid JSON, not
        # conformance to our schema — unlike Claude's native output_config.format.
        # So the schema is spelled out in the prompt text, and the response is
        # validated locally, with one retry (re-prompted with the validation error)
        # before giving up — small local models don't reliably get this right first try.
        model = build_model_from_schema(schema)

        response = await self._client.post("/api/chat", json=self._build_structured_body(prompt, schema))
        response.raise_for_status()
        content = response.json().get("message", {}).get("content", "")
        try:
            return self._parse_and_validate(content, model)
        except (json.JSONDecodeError, ValidationError) as first_error:
            retry_response = await self._client.post(
                "/api/chat",
                json=self._build_structured_body(prompt, schema, previous_error=str(first_error)),
            )
            retry_response.raise_for_status()
            retry_content = retry_response.json().get("message", {}).get("content", "")
            try:
                return self._parse_and_validate(retry_content, model)
            except (json.JSONDecodeError, ValidationError) as second_error:
                raise RuntimeError(
                    "Ollama did not return valid structured JSON after a retry: "
                    f"{second_error}"
                ) from second_error

    def _build_structured_body(self, prompt: Prompt, schema: dict, previous_error: str | None = None) -> dict:
        example = build_example_from_schema(schema)
        schema_instruction = (
            "Respond with ONLY one JSON object shaped exactly like this example — same "
            "keys, same nesting, at every level. Never invent, rename, split, or add any "
            "key that isn't already in the example, no matter how the request is worded — "
            "any requirements or preferences in the request affect the *content* you put "
            "inside the existing keys, never the *key names themselves*. Put all repeated "
            "items of one kind into the single list the example already shows for them. "
            "Fill it in with real content. No prose, no markdown code fences:\n"
            f"{json.dumps(example, indent=2)}"
        )
        messages = [{"role": "system", "content": f"{prompt.system_prompt}\n\n{schema_instruction}"}]
        messages.extend({"role": turn.role, "content": turn.content} for turn in prompt.conversation_history)

        question = prompt.question
        if previous_error:
            question = (
                f"{question}\n\nYour previous response was invalid: {previous_error}. "
                "Return corrected JSON only."
            )
        messages.append({"role": "user", "content": question})

        return {"model": self._model, "messages": messages, "format": "json", "stream": False}

    @staticmethod
    def _parse_and_validate(content: str, model) -> dict:
        data = json.loads(content)
        validated = model.model_validate(data)
        return validated.model_dump()

    async def aclose(self) -> None:
        await self._client.aclose()
