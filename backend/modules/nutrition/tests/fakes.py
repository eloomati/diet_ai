from uuid import UUID

from backend.modules.nutrition.domain import NutritionProfile


class InMemoryNutritionProfileRepository:
    def __init__(self) -> None:
        self._by_user_id: dict[UUID, NutritionProfile] = {}

    async def get_by_user_id(self, user_id: UUID) -> NutritionProfile | None:
        return self._by_user_id.get(user_id)

    async def save(self, profile: NutritionProfile) -> None:
        self._by_user_id[profile.user_id] = profile
