from backend.modules.ai.domain import Prompt, PromptTurn
from backend.modules.conversation.domain import Conversation, MessageRole


class PromptBuilder:
    @staticmethod
    def build(conversation: Conversation, question: str) -> Prompt:
        history = tuple(
            PromptTurn(
                role="user" if message.role == MessageRole.USER else "assistant",
                content=message.content,
            )
            for message in conversation.messages
            if message.role != MessageRole.SYSTEM
        )
        return Prompt(
            question=question,
            category=conversation.category.value,
            conversation_history=history,
        )
