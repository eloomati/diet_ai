from uuid import UUID, uuid4

import pytest

from backend.modules.ai.tests.fakes import FakeLLMProvider
from backend.modules.nutrition.application import (
    CreateNutritionProfileCommand,
    CreateNutritionProfileUseCase,
    GenerateDietPlanCommand,
    GenerateDietPlanUseCase,
    NutritionProfileNotFoundError,
    WeeklyObligationInput,
)
from backend.modules.nutrition.domain import DayOfWeek
from backend.modules.nutrition.tests.fakes import (
    InMemoryDietPlanRepository,
    InMemoryNutritionProfileRepository,
)

# Every weekday obligated, same window — so a colliding-time test doesn't depend
# on which actual weekday "day_number=1" (== today, per GenerateDietPlanUseCase's
# resolve_weekday assumption) lands on when the test happens to run.
_FULL_WEEK_WORK_OBLIGATIONS = tuple(
    WeeklyObligationInput(day_of_week=day.value, start_time="09:00", end_time="17:00", label="Work")
    for day in DayOfWeek
)


def _plan_dict(duration_days: int, meal_time: str | None = None) -> dict:
    meal = {
        "name": "Oatmeal",
        "calories": 400,
        "protein": 20,
        "carbohydrates": 60,
        "fat": 10,
    }
    if meal_time is not None:
        meal["time"] = meal_time
    return {
        "days": [
            {"day_number": day, "meals": [meal]} for day in range(1, duration_days + 1)
        ]
    }


async def _create_profile(
    repo: InMemoryNutritionProfileRepository,
    user_id,
    weekly_obligations: tuple[WeeklyObligationInput, ...] = (),
) -> None:
    await CreateNutritionProfileUseCase(repo).execute(
        CreateNutritionProfileCommand(
            user_id=user_id,
            age=29,
            height_cm=187,
            weight_kg=80,
            activity_level="HIGH",
            goal="MUSCLE_GAIN",
            diet_type="VEGETARIAN",
            weekly_obligations=weekly_obligations,
        )
    )


@pytest.mark.asyncio
async def test_generate_diet_plan_returns_structured_plan() -> None:
    profile_repo = InMemoryNutritionProfileRepository()
    plan_repo = InMemoryDietPlanRepository()
    user_id = uuid4()
    await _create_profile(profile_repo, user_id)
    llm = FakeLLMProvider(canned_structured_response=_plan_dict(3))

    use_case = GenerateDietPlanUseCase(plan_repo, profile_repo, llm)
    result = await use_case.execute(
        GenerateDietPlanCommand(user_id=user_id, duration_days=3, requirements=("high protein",))
    )

    assert result.duration_days == 3
    assert len(result.days) == 3
    assert result.goal == "MUSCLE_GAIN"
    assert result.diet_type == "VEGETARIAN"
    assert result.requirements == ("high protein",)
    assert result.days[0].meals[0].name == "Oatmeal"


@pytest.mark.asyncio
async def test_generate_diet_plan_persists_the_plan() -> None:
    profile_repo = InMemoryNutritionProfileRepository()
    plan_repo = InMemoryDietPlanRepository()
    user_id = uuid4()
    await _create_profile(profile_repo, user_id)
    llm = FakeLLMProvider(canned_structured_response=_plan_dict(2))

    result = await GenerateDietPlanUseCase(plan_repo, profile_repo, llm).execute(
        GenerateDietPlanCommand(user_id=user_id, duration_days=2)
    )

    stored = await plan_repo.get_by_id(UUID(result.plan_id))
    assert stored is not None
    assert stored.user_id == user_id


@pytest.mark.asyncio
async def test_generate_diet_plan_uses_profile_in_prompt() -> None:
    profile_repo = InMemoryNutritionProfileRepository()
    plan_repo = InMemoryDietPlanRepository()
    user_id = uuid4()
    await _create_profile(profile_repo, user_id)
    llm = FakeLLMProvider(canned_structured_response=_plan_dict(1))

    await GenerateDietPlanUseCase(plan_repo, profile_repo, llm).execute(
        GenerateDietPlanCommand(user_id=user_id, duration_days=1)
    )

    assert llm.last_prompt is not None
    assert "MUSCLE_GAIN" in llm.last_prompt.question
    assert llm.last_schema is not None
    assert "days" in llm.last_schema["properties"]


@pytest.mark.asyncio
async def test_generate_diet_plan_without_profile_raises() -> None:
    profile_repo = InMemoryNutritionProfileRepository()
    plan_repo = InMemoryDietPlanRepository()
    llm = FakeLLMProvider(canned_structured_response=_plan_dict(1))

    with pytest.raises(NutritionProfileNotFoundError):
        await GenerateDietPlanUseCase(plan_repo, profile_repo, llm).execute(
            GenerateDietPlanCommand(user_id=uuid4(), duration_days=1)
        )


@pytest.mark.asyncio
async def test_generate_diet_plan_keeps_ai_suggested_time_when_no_obligations() -> None:
    profile_repo = InMemoryNutritionProfileRepository()
    plan_repo = InMemoryDietPlanRepository()
    user_id = uuid4()
    await _create_profile(profile_repo, user_id)
    llm = FakeLLMProvider(canned_structured_response=_plan_dict(1, meal_time="08:00"))

    result = await GenerateDietPlanUseCase(plan_repo, profile_repo, llm).execute(
        GenerateDietPlanCommand(user_id=user_id, duration_days=1)
    )

    assert result.days[0].meals[0].time == "08:00"


@pytest.mark.asyncio
async def test_generate_diet_plan_defaults_meal_time_to_none_when_ai_omits_it() -> None:
    profile_repo = InMemoryNutritionProfileRepository()
    plan_repo = InMemoryDietPlanRepository()
    user_id = uuid4()
    await _create_profile(profile_repo, user_id)
    llm = FakeLLMProvider(canned_structured_response=_plan_dict(1))

    result = await GenerateDietPlanUseCase(plan_repo, profile_repo, llm).execute(
        GenerateDietPlanCommand(user_id=user_id, duration_days=1)
    )

    assert result.days[0].meals[0].time is None


@pytest.mark.asyncio
async def test_generate_diet_plan_clamps_meal_time_colliding_with_obligation() -> None:
    profile_repo = InMemoryNutritionProfileRepository()
    plan_repo = InMemoryDietPlanRepository()
    user_id = uuid4()
    await _create_profile(profile_repo, user_id, weekly_obligations=_FULL_WEEK_WORK_OBLIGATIONS)
    llm = FakeLLMProvider(canned_structured_response=_plan_dict(1, meal_time="12:00"))

    result = await GenerateDietPlanUseCase(plan_repo, profile_repo, llm).execute(
        GenerateDietPlanCommand(user_id=user_id, duration_days=1)
    )

    # 12:00 falls inside the 09:00-17:00 work obligation on every weekday, so it
    # must be shifted to the obligation's end regardless of which day this runs on.
    assert result.days[0].meals[0].time == "17:00"


@pytest.mark.asyncio
async def test_generate_diet_plan_keeps_time_outside_obligation_window() -> None:
    profile_repo = InMemoryNutritionProfileRepository()
    plan_repo = InMemoryDietPlanRepository()
    user_id = uuid4()
    await _create_profile(profile_repo, user_id, weekly_obligations=_FULL_WEEK_WORK_OBLIGATIONS)
    llm = FakeLLMProvider(canned_structured_response=_plan_dict(1, meal_time="07:00"))

    result = await GenerateDietPlanUseCase(plan_repo, profile_repo, llm).execute(
        GenerateDietPlanCommand(user_id=user_id, duration_days=1)
    )

    assert result.days[0].meals[0].time == "07:00"


@pytest.mark.asyncio
async def test_generate_diet_plan_drops_malformed_ai_time_instead_of_failing() -> None:
    profile_repo = InMemoryNutritionProfileRepository()
    plan_repo = InMemoryDietPlanRepository()
    user_id = uuid4()
    await _create_profile(profile_repo, user_id)
    llm = FakeLLMProvider(canned_structured_response=_plan_dict(1, meal_time="not-a-time"))

    result = await GenerateDietPlanUseCase(plan_repo, profile_repo, llm).execute(
        GenerateDietPlanCommand(user_id=user_id, duration_days=1)
    )

    assert result.days[0].meals[0].time is None
