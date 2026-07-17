from backend.modules.nutrition.application.dto.diet_plan_dto import DietPlanResult, GetDietPlanQuery
from backend.modules.nutrition.application.use_cases.exceptions import DietPlanNotFoundError
from backend.modules.nutrition.domain import DietPlanRepository


class GetDietPlanUseCase:
    def __init__(self, repository: DietPlanRepository) -> None:
        self._repository = repository

    async def execute(self, query: GetDietPlanQuery) -> DietPlanResult:
        plan = await self._repository.get_by_id(query.plan_id)
        if plan is None or plan.user_id != query.user_id:
            raise DietPlanNotFoundError("Diet plan not found.")

        return DietPlanResult.from_domain(plan)
