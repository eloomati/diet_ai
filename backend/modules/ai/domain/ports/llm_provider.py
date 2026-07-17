from abc import ABC, abstractmethod

from backend.modules.ai.domain.value_objects.ai_response import AIResponse
from backend.modules.ai.domain.value_objects.prompt import Prompt


class LLMProvider(ABC):
    @abstractmethod
    async def generate_response(self, prompt: Prompt) -> AIResponse:
        raise NotImplementedError

    async def generate_structured_response(self, prompt: Prompt, schema: dict) -> dict:
        """Return a dict validated against `schema`. Optional capability — implemented by
        providers that support structured output (see Stage 3 of Phase 7 in the roadmap)."""
        raise NotImplementedError(f"{type(self).__name__} does not support structured responses.")
