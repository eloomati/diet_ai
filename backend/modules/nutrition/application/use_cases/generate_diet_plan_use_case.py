from backend.modules.ai.application.diet_plan_prompt_builder import DietPlanPromptBuilder
from backend.modules.ai.domain import LLMProvider
from backend.modules.nutrition.application.dto.diet_plan_dto import (
    DietPlanResult,
    GenerateDietPlanCommand,
)
from backend.modules.nutrition.application.use_cases.exceptions import (
    NutritionProfileNotFoundError,
)
from backend.modules.nutrition.domain import (
    DietDay,
    DietPlan,
    DietPlanRepository,
    Meal,
    NutritionProfileRepository,
)


class GenerateDietPlanUseCase:
    def __init__(
        self,
        diet_plan_repository: DietPlanRepository,
        nutrition_profile_repository: NutritionProfileRepository,
        llm_provider: LLMProvider,
    ) -> None:
        self._diet_plan_repository = diet_plan_repository
        self._nutrition_profile_repository = nutrition_profile_repository
        self._llm_provider = llm_provider

    async def execute(self, command: GenerateDietPlanCommand) -> DietPlanResult:
        profile = await self._nutrition_profile_repository.get_by_user_id(command.user_id)
        if profile is None:
            raise NutritionProfileNotFoundError(
                "A nutrition profile is required before generating a diet plan."
            )

        requirements = tuple(command.requirements or ())
        prompt = DietPlanPromptBuilder.build(
            user_profile_text=profile.as_prompt_text(),
            duration_days=command.duration_days,
            requirements=requirements,
        )
        schema = DietPlanPromptBuilder.build_schema()
        raw_plan = await self._llm_provider.generate_structured_response(prompt, schema)

        days = tuple(
            DietDay(
                day_number=raw_day["day_number"],
                meals=tuple(Meal(**raw_meal) for raw_meal in raw_day["meals"]),
            )
            for raw_day in raw_plan["days"]
        )
        plan = DietPlan.create(
            user_id=command.user_id,
            goal=profile.goal,
            diet_type=profile.diet_type,
            duration_days=command.duration_days,
            days=days,
            requirements=requirements,
        )
        await self._diet_plan_repository.save(plan)

        return DietPlanResult.from_domain(plan)
