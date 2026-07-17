from abc import ABC, abstractmethod

from backend.modules.ai.domain.value_objects.ai_response import AIResponse
from backend.modules.ai.domain.value_objects.prompt import Prompt


class LLMProvider(ABC):
    @abstractmethod
    async def generate_response(self, prompt: Prompt) -> AIResponse:
        raise NotImplementedError
