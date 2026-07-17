from abc import ABC, abstractmethod
from uuid import UUID

from backend.modules.conversation.domain.entities.conversation import Conversation


class ConversationRepository(ABC):
    @abstractmethod
    async def get_by_id(self, conversation_id: UUID) -> Conversation | None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_user(self, user_id: UUID) -> list[Conversation]:
        raise NotImplementedError

    @abstractmethod
    async def save(self, conversation: Conversation) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, conversation_id: UUID) -> None:
        raise NotImplementedError
