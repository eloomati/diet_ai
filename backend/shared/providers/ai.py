class LLMProvider:
    """Abstrakcyjna klasa dla AI providera. Będzie implementowana w identity/infrastructure."""

    async def generate_response(self, prompt: str) -> str:
        raise NotImplementedError


class MockLLMProvider(LLMProvider):
    """Mock provider do developmentu/testów bez rzeczywistego AI."""

    async def generate_response(self, prompt: str) -> str:
        return f"Mock AI response to: {prompt[:50]}..."