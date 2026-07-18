from backend.modules.nutrition.application.dto.diet_plan_dto import (
    DietPlanSummaryResult,
    ListDietPlansQuery,
)
from backend.modules.nutrition.domain import DietPlanRepository


class ListDietPlansUseCase:
    def __init__(self, repository: DietPlanRepository) -> None:
        self._repository = repository

    async def execute(self, query: ListDietPlansQuery) -> list[DietPlanSummaryResult]:
        plans = await self._repository.list_by_user_id(
            query.user_id, start_date=query.start_date, end_date=query.end_date
        )
        return [DietPlanSummaryResult.from_domain(plan) for plan in plans]
