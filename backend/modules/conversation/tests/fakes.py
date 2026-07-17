from uuid import UUID

from backend.modules.conversation.domain import Conversation


class InMemoryConversationRepository:
    def __init__(self) -> None:
        self._by_id: dict[UUID, Conversation] = {}

    async def get_by_id(self, conversation_id: UUID) -> Conversation | None:
        return self._by_id.get(conversation_id)

    async def list_by_user(self, user_id: UUID) -> list[Conversation]:
        return [c for c in self._by_id.values() if c.user_id == user_id]

    async def save(self, conversation: Conversation) -> None:
        self._by_id[conversation.id] = conversation

    async def delete(self, conversation_id: UUID) -> None:
        self._by_id.pop(conversation_id, None)
