import time

import anthropic

from backend.modules.ai.domain import AIResponse, LLMProvider, Prompt


class ClaudeProvider(LLMProvider):
    def __init__(
        self,
        api_key: str,
        model: str = "claude-opus-4-8",
        client: anthropic.AsyncAnthropic | None = None,
    ) -> None:
        self._model = model
        self._client = client or anthropic.AsyncAnthropic(api_key=api_key)

    async def generate_response(self, prompt: Prompt) -> AIResponse:
        started_at = time.monotonic()
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=self._build_system(prompt),
            messages=self._build_messages(prompt),
        )
        execution_time = time.monotonic() - started_at

        content = next((block.text for block in response.content if block.type == "text"), "")

        return AIResponse(
            content=content,
            model=response.model,
            tokens=response.usage.output_tokens,
            execution_time=execution_time,
        )

    def _build_system(self, prompt: Prompt) -> str:
        parts = [f"You are a helpful assistant for the category: {prompt.category}."]
        if prompt.user_profile:
            parts.append(f"User profile: {prompt.user_profile}")
        if prompt.system_context:
            parts.append(prompt.system_context)
        return "\n".join(parts)

    def _build_messages(self, prompt: Prompt) -> list[dict[str, str]]:
        messages = [{"role": turn.role, "content": turn.content} for turn in prompt.conversation_history]
        messages.append({"role": "user", "content": prompt.question})
        return messages
