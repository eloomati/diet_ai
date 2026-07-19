from abc import ABC, abstractmethod
from uuid import UUID

from backend.modules.dietitian.domain.entities.dietitian_profile import DietitianProfile


class DietitianProfileRepository(ABC):
    @abstractmethod
    async def get_by_user_id(self, user_id: UUID) -> DietitianProfile | None:
        raise NotImplementedError

    @abstractmethod
    async def save(self, profile: DietitianProfile) -> None:
        raise NotImplementedError
