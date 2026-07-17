from backend.modules.ai.domain import Prompt
from backend.modules.conversation.domain import Conversation


class PromptBuilder:
    @staticmethod
    def build(conversation: Conversation, question: str) -> Prompt:
        history = tuple(
            f"{message.role.value}: {message.content}" for message in conversation.messages
        )
        return Prompt(
            question=question,
            category=conversation.category.value,
            conversation_history=history,
        )
