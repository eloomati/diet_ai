from backend.modules.ai.domain import Prompt, PromptTurn
from backend.modules.conversation.domain import Conversation, MessageRole

_BASE_SYSTEM_PROMPT = (
    "You are the Diet AI assistant, a nutrition and fitness expert. Give practical, "
    "specific, evidence-based advice — concrete meals, portions, macros, or routines "
    "rather than generic platitudes. You are not a substitute for a doctor or "
    "registered dietitian: say so plainly when a question touches on medical "
    "conditions, medication interactions, or supplement safety, and recommend "
    "professional advice for those cases."
)

# Keyed by ConversationCategory value — kept as plain strings here (not the enum
# itself) so the ai domain stays decoupled from the conversation domain, same
# reasoning as Prompt.categories holding plain strings, not the enum.
_CATEGORY_GUIDANCE: dict[str, str] = {
    "BREAKFAST": (
        "Focus on breakfast-appropriate meals: quick to prepare, macro-balanced, "
        "realistic for a morning routine."
    ),
    "DIET": "Focus on overall dietary patterns and calorie/macro balance for the user's stated goal.",
    "FITNESS": "Connect nutrition advice to general fitness and body-composition goals.",
    "RUNNING": (
        "Focus on endurance-sport nutrition: pre-/post-run fueling, hydration, and "
        "carbohydrate timing."
    ),
    "GYM": (
        "Focus on nutrition supporting strength training: protein timing/intake and "
        "recovery."
    ),
    "HEALTH": (
        "Focus on general wellness and how nutrition supports it; flag anything that "
        "sounds like a medical concern rather than answering it directly."
    ),
    "SUPPLEMENTS": (
        "Be cautious and evidence-based about supplements — note interactions and "
        "risks, and recommend consulting a professional before starting a new one."
    ),
    "GENERAL": "Use your judgement about which nutrition/fitness angle is most relevant.",
}


class PromptBuilder:
    @staticmethod
    def build(conversation: Conversation, question: str, user_profile: str | None = None) -> Prompt:
        history = tuple(
            PromptTurn(
                role="user" if message.role == MessageRole.USER else "assistant",
                content=message.content,
            )
            for message in conversation.messages
            if message.role != MessageRole.SYSTEM
        )
        categories = tuple(c.value for c in conversation.categories)
        return Prompt(
            question=question,
            categories=categories,
            system_prompt=PromptBuilder._build_system_prompt(categories, user_profile),
            conversation_history=history,
        )

    @staticmethod
    def _build_system_prompt(categories: tuple[str, ...], user_profile: str | None) -> str:
        parts = [_BASE_SYSTEM_PROMPT]

        for category in categories:
            guidance = _CATEGORY_GUIDANCE.get(category)
            if guidance and guidance not in parts:
                parts.append(guidance)

        if user_profile:
            parts.append(f"User profile: {user_profile}")

        return "\n\n".join(parts)
