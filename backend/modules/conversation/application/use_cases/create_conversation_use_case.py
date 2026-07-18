from backend.modules.conversation.application.dto.create_conversation_dto import (
    CreateConversationCommand,
    CreateConversationResult,
)
from backend.modules.conversation.domain import Conversation, ConversationCategory, ConversationRepository


class CreateConversationUseCase:
    def __init__(self, conversation_repository: ConversationRepository) -> None:
        self._conversation_repository = conversation_repository

    async def execute(self, command: CreateConversationCommand) -> CreateConversationResult:
        conversation = Conversation.create(
            user_id=command.user_id,
            title=command.title,
            categories=[ConversationCategory(c) for c in command.categories],
        )

        await self._conversation_repository.save(conversation)

        return CreateConversationResult(
            conversation_id=str(conversation.id),
            title=conversation.title,
            categories=[c.value for c in conversation.categories],
            status=conversation.status.value,
        )
