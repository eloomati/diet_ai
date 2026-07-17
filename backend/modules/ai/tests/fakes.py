from backend.modules.ai.domain import AIResponse, LLMProvider, Prompt


class FakeLLMProvider(LLMProvider):
    def __init__(
        self,
        canned_response: str = "This is a mock AI response.",
        canned_structured_response: dict | None = None,
    ) -> None:
        self._canned_response = canned_response
        self._canned_structured_response = canned_structured_response
        self.last_prompt: Prompt | None = None
        self.last_schema: dict | None = None

    async def generate_response(self, prompt: Prompt) -> AIResponse:
        self.last_prompt = prompt
        return AIResponse(
            content=self._canned_response,
            model="fake-llm",
            tokens=len(self._canned_response.split()),
            execution_time=0.0,
        )

    async def generate_structured_response(self, prompt: Prompt, schema: dict) -> dict:
        self.last_prompt = prompt
        self.last_schema = schema
        if self._canned_structured_response is None:
            raise ValueError("FakeLLMProvider has no canned_structured_response configured.")
        return self._canned_structured_response
