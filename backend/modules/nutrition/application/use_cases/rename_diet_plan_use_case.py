from backend.modules.nutrition.application.dto.diet_plan_dto import (
    DietPlanResult,
    RenameDietPlanCommand,
)
from backend.modules.nutrition.application.use_cases.exceptions import DietPlanNotFoundError
from backend.modules.nutrition.domain import DietPlanRepository


class RenameDietPlanUseCase:
    def __init__(self, repository: DietPlanRepository) -> None:
        self._repository = repository

    async def execute(self, command: RenameDietPlanCommand) -> DietPlanResult:
        plan = await self._repository.get_by_id(command.plan_id)
        if plan is None or plan.user_id != command.user_id:
            raise DietPlanNotFoundError("Diet plan not found.")

        plan.rename(command.name)
        await self._repository.save(plan)

        return DietPlanResult.from_domain(plan)
