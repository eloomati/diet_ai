from backend.modules.ai.domain import AIResponse, LLMProvider, Prompt


class MockLLMProvider(LLMProvider):
    """Deterministic dev/test provider — no network calls."""

    async def generate_response(self, prompt: Prompt) -> AIResponse:
        content = f"Mock AI response for category={prompt.category}: {prompt.question[:50]}..."
        return AIResponse(content=content, model="mock", tokens=len(content.split()), execution_time=0.0)
