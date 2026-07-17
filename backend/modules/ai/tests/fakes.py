from backend.modules.ai.domain import AIResponse, LLMProvider, Prompt


class FakeLLMProvider(LLMProvider):
    def __init__(self, canned_response: str = "This is a mock AI response.") -> None:
        self._canned_response = canned_response

    async def generate_response(self, prompt: Prompt) -> AIResponse:
        return AIResponse(
            content=self._canned_response,
            model="fake-llm",
            tokens=len(self._canned_response.split()),
            execution_time=0.0,
        )
