from backend.modules.ai.domain import Prompt

_SYSTEM_PROMPT = (
    "You are a professional dietitian assistant. Generate a structured, realistic "
    "multi-day meal plan tailored to the given user profile, goal, and diet type. "
    "Keep portions and macros plausible for the stated goal — do not invent extreme "
    "or unsafe calorie targets."
)


class DietPlanPromptBuilder:
    @staticmethod
    def build(user_profile_text: str, duration_days: int, requirements: tuple[str, ...] = ()) -> Prompt:
        requirements_text = "; ".join(requirements) if requirements else "none"
        question = (
            f"Generate a {duration_days}-day diet plan for this user: {user_profile_text}. "
            f"Additional requirements: {requirements_text}."
        )
        return Prompt(question=question, category="DIET", system_prompt=_SYSTEM_PROMPT)

    @staticmethod
    def build_schema() -> dict:
        # No minItems/maxItems on the "days" array: Claude's structured-output schema
        # support excludes complex array constraints. The exact day count is instead
        # enforced by DietPlan.create() after parsing the response.
        return {
            "type": "object",
            "properties": {
                "days": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "day_number": {"type": "integer"},
                            "meals": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "calories": {"type": "number"},
                                        "protein": {"type": "number"},
                                        "carbohydrates": {"type": "number"},
                                        "fat": {"type": "number"},
                                    },
                                    "required": [
                                        "name",
                                        "calories",
                                        "protein",
                                        "carbohydrates",
                                        "fat",
                                    ],
                                    "additionalProperties": False,
                                },
                            },
                        },
                        "required": ["day_number", "meals"],
                        "additionalProperties": False,
                    },
                },
            },
            "required": ["days"],
            "additionalProperties": False,
        }
