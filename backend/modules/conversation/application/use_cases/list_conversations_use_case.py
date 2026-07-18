from backend.modules.conversation.application.dto.list_conversations_dto import (
    ConversationSummary,
    ListConversationsQuery,
)
from backend.modules.conversation.domain import ConversationRepository


class ListConversationsUseCase:
    def __init__(self, conversation_repository: ConversationRepository) -> None:
        self._conversation_repository = conversation_repository

    async def execute(self, query: ListConversationsQuery) -> list[ConversationSummary]:
        conversations = await self._conversation_repository.list_by_user(query.user_id)

        return [
            ConversationSummary(
                conversation_id=str(conversation.id),
                title=conversation.title,
                categories=[c.value for c in conversation.categories],
                status=conversation.status.value,
                updated_at=conversation.updated_at.isoformat(),
            )
            for conversation in conversations
        ]
