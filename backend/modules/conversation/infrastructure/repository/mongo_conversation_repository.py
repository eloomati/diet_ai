from uuid import UUID

from backend.modules.conversation.domain.entities.conversation import Conversation
from backend.modules.conversation.domain.repositories.conversation_repository import (
    ConversationRepository,
)
from backend.modules.conversation.infrastructure.documents.conversation_document import (
    ConversationDocument,
)
from backend.modules.conversation.infrastructure.mappers.conversation_mapper import (
    ConversationMapper,
)


class MongoConversationRepository(ConversationRepository):
    async def get_by_id(self, conversation_id: UUID) -> Conversation | None:
        document = await ConversationDocument.get(conversation_id)
        return ConversationMapper.to_domain(document) if document else None

    async def list_by_user(self, user_id: UUID) -> list[Conversation]:
        documents = await ConversationDocument.find(
            ConversationDocument.user_id == user_id
        ).to_list()
        return [ConversationMapper.to_domain(document) for document in documents]

    async def save(self, conversation: Conversation) -> None:
        document = ConversationMapper.to_document(conversation)
        await document.save()

    async def delete(self, conversation_id: UUID) -> None:
        document = await ConversationDocument.get(conversation_id)
        if document is not None:
            await document.delete()
