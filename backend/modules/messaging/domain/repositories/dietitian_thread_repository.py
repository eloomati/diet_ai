from abc import ABC, abstractmethod
from uuid import UUID

from backend.modules.messaging.domain.entities.dietitian_thread import DietitianThread


class DietitianThreadRepository(ABC):
    @abstractmethod
    async def get_by_id(self, thread_id: UUID) -> DietitianThread | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_participants(
        self, user_id: UUID, dietitian_id: UUID
    ) -> DietitianThread | None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_participant(self, user_id: UUID) -> list[DietitianThread]:
        raise NotImplementedError

    @abstractmethod
    async def save(self, thread: DietitianThread) -> None:
        raise NotImplementedError
