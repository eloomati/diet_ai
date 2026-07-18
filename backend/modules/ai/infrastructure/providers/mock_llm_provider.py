import re

from backend.modules.ai.domain import AIResponse, LLMProvider, Prompt

_DURATION_DAYS_PATTERN = re.compile(r"(\d+)-day diet plan")


class MockLLMProvider(LLMProvider):
    """Deterministic dev/test provider — no network calls."""

    async def generate_response(self, prompt: Prompt) -> AIResponse:
        content = f"Mock AI response for categories={','.join(prompt.categories)}: {prompt.question[:50]}..."
        return AIResponse(content=content, model="mock", tokens=len(content.split()), execution_time=0.0)

    async def generate_structured_response(self, prompt: Prompt, schema: dict) -> dict:
        match = _DURATION_DAYS_PATTERN.search(prompt.question)
        duration_days = int(match.group(1)) if match else 1
        return {
            "days": [
                {
                    "day_number": day,
                    "meals": [
                        {
                            "name": "Mock meal",
                            "calories": 500,
                            "protein": 30,
                            "carbohydrates": 50,
                            "fat": 15,
                        }
                    ],
                }
                for day in range(1, duration_days + 1)
            ]
        }
