from backend.modules.conversation.application.dto.delete_conversation_dto import (
    DeleteConversationCommand,
)
from backend.modules.conversation.application.use_cases.exceptions import ConversationNotFoundError
from backend.modules.conversation.domain import ConversationRepository


class DeleteConversationUseCase:
    def __init__(self, conversation_repository: ConversationRepository) -> None:
        self._conversation_repository = conversation_repository

    async def execute(self, command: DeleteConversationCommand) -> None:
        conversation = await self._conversation_repository.get_by_id(command.conversation_id)
        if conversation is None or conversation.user_id != command.user_id:
            raise ConversationNotFoundError("Conversation not found.")

        await self._conversation_repository.delete(conversation.id)
