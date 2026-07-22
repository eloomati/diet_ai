from abc import ABC, abstractmethod
from uuid import UUID

from backend.modules.messaging.domain.entities.dietitian_message import DietitianMessage


class DietitianMessageRepository(ABC):
    @abstractmethod
    async def list_by_thread_id(self, thread_id: UUID) -> list[DietitianMessage]:
        raise NotImplementedError

    @abstractmethod
    async def save(self, message: DietitianMessage) -> None:
        raise NotImplementedError
