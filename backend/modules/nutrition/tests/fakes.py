from uuid import UUID

from backend.modules.nutrition.domain import DietPlan, NutritionProfile


class InMemoryNutritionProfileRepository:
    def __init__(self) -> None:
        self._by_user_id: dict[UUID, NutritionProfile] = {}

    async def get_by_user_id(self, user_id: UUID) -> NutritionProfile | None:
        return self._by_user_id.get(user_id)

    async def save(self, profile: NutritionProfile) -> None:
        self._by_user_id[profile.user_id] = profile


class InMemoryDietPlanRepository:
    def __init__(self) -> None:
        self._by_id: dict[UUID, DietPlan] = {}

    async def get_by_id(self, plan_id: UUID) -> DietPlan | None:
        return self._by_id.get(plan_id)

    async def list_by_user_id(self, user_id: UUID) -> list[DietPlan]:
        plans = [plan for plan in self._by_id.values() if plan.user_id == user_id]
        return sorted(plans, key=lambda plan: plan.created_at, reverse=True)

    async def save(self, plan: DietPlan) -> None:
        self._by_id[plan.id] = plan
