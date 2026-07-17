from abc import ABC, abstractmethod
from uuid import UUID

from backend.modules.nutrition.domain.entities.nutrition_profile import NutritionProfile


class NutritionProfileRepository(ABC):
    @abstractmethod
    async def get_by_user_id(self, user_id: UUID) -> NutritionProfile | None:
        raise NotImplementedError

    @abstractmethod
    async def save(self, profile: NutritionProfile) -> None:
        raise NotImplementedError
