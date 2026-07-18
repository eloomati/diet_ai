from datetime import UTC, date, datetime, time

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
    MealScheduler,
    NutritionProfileRepository,
    WeeklyObligation,
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

        # day_number=1 is treated as "today" — the natural reading of "generate my
        # plan starting now" — so weekly (day-of-week-based) obligations can be
        # checked against it. See docs/architecture.md for this assumption.
        plan_start_date = datetime.now(UTC).date()
        days = tuple(
            DietDay(
                day_number=raw_day["day_number"],
                meals=tuple(
                    self._build_meal(
                        raw_meal, raw_day["day_number"], plan_start_date, profile.weekly_obligations
                    )
                    for raw_meal in raw_day["meals"]
                ),
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

    @staticmethod
    def _build_meal(
        raw_meal: dict,
        day_number: int,
        plan_start_date: date,
        weekly_obligations: tuple[WeeklyObligation, ...],
    ) -> Meal:
        meal_time: time | None = None
        raw_time = raw_meal.get("time")
        if raw_time:
            try:
                meal_time = time.fromisoformat(raw_time)
            except ValueError:
                # A small local model can still produce a malformed time string
                # despite the prompt's instructions — drop it rather than fail the
                # whole generation over a cosmetic field.
                meal_time = None

        if meal_time is not None and weekly_obligations:
            weekday = MealScheduler.resolve_weekday(plan_start_date, day_number)
            meal_time = MealScheduler.clamp_meal_time(meal_time, weekday, weekly_obligations)

        return Meal(
            name=raw_meal["name"],
            calories=raw_meal["calories"],
            protein=raw_meal["protein"],
            carbohydrates=raw_meal["carbohydrates"],
            fat=raw_meal["fat"],
            time=meal_time,
        )
