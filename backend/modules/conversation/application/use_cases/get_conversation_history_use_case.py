from backend.modules.conversation.application.dto.get_conversation_history_dto import (
    GetConversationHistoryQuery,
    GetConversationHistoryResult,
    MessageView,
)
from backend.modules.conversation.application.use_cases.exceptions import ConversationNotFoundError
from backend.modules.conversation.domain import ConversationRepository


class GetConversationHistoryUseCase:
    def __init__(self, conversation_repository: ConversationRepository) -> None:
        self._conversation_repository = conversation_repository

    async def execute(self, query: GetConversationHistoryQuery) -> GetConversationHistoryResult:
        conversation = await self._conversation_repository.get_by_id(query.conversation_id)
        if conversation is None or conversation.user_id != query.user_id:
            raise ConversationNotFoundError("Conversation not found.")

        return GetConversationHistoryResult(
            conversation_id=str(conversation.id),
            title=conversation.title,
            categories=[c.value for c in conversation.categories],
            status=conversation.status.value,
            messages=[
                MessageView(
                    id=str(message.id),
                    role=message.role.value,
                    content=message.content,
                    created_at=message.created_at.isoformat(),
                )
                for message in conversation.messages
            ],
        )
