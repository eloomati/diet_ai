from datetime import time
from uuid import UUID, uuid4

import pytest

from backend.modules.ai.tests.fakes import FakeLLMProvider
from backend.modules.nutrition.application import (
    CreateNutritionProfileCommand,
    CreateNutritionProfileUseCase,
    DietPlanNotFoundError,
    GenerateDietPlanCommand,
    GenerateDietPlanUseCase,
    RescheduleMealCommand,
    RescheduleMealUseCase,
)
from backend.modules.nutrition.domain import MealNotFoundError
from backend.modules.nutrition.tests.fakes import (
    InMemoryDietPlanRepository,
    InMemoryNutritionProfileRepository,
)


def _plan_dict(duration_days: int) -> dict:
    return {
        "days": [
            {
                "day_number": day,
                "meals": [
                    {"name": "Oatmeal", "calories": 400, "protein": 20, "carbohydrates": 60, "fat": 10}
                ],
            }
            for day in range(1, duration_days + 1)
        ]
    }


async def _generate_plan(plan_repo, profile_repo, user_id, duration_days: int = 1):
    await CreateNutritionProfileUseCase(profile_repo).execute(
        CreateNutritionProfileCommand(
            user_id=user_id,
            age=29,
            height_cm=187,
            weight_kg=80,
            activity_level="HIGH",
            goal="MUSCLE_GAIN",
            diet_type="VEGETARIAN",
        )
    )
    llm = FakeLLMProvider(canned_structured_response=_plan_dict(duration_days))
    return await GenerateDietPlanUseCase(plan_repo, profile_repo, llm).execute(
        GenerateDietPlanCommand(user_id=user_id, duration_days=duration_days)
    )


@pytest.mark.asyncio
async def test_reschedule_meal_updates_the_time() -> None:
    plan_repo = InMemoryDietPlanRepository()
    user_id = uuid4()
    created = await _generate_plan(plan_repo, InMemoryNutritionProfileRepository(), user_id)

    result = await RescheduleMealUseCase(plan_repo).execute(
        RescheduleMealCommand(
            user_id=user_id,
            plan_id=UUID(created.plan_id),
            day_number=1,
            meal_name="Oatmeal",
            new_time=time(8, 0),
        )
    )

    assert result.days[0].meals[0].time == "08:00"


@pytest.mark.asyncio
async def test_reschedule_meal_persists_the_change() -> None:
    plan_repo = InMemoryDietPlanRepository()
    user_id = uuid4()
    created = await _generate_plan(plan_repo, InMemoryNutritionProfileRepository(), user_id)

    await RescheduleMealUseCase(plan_repo).execute(
        RescheduleMealCommand(
            user_id=user_id,
            plan_id=UUID(created.plan_id),
            day_number=1,
            meal_name="Oatmeal",
            new_time=time(8, 0),
        )
    )

    stored = await plan_repo.get_by_id(UUID(created.plan_id))
    assert stored.days[0].meals[0].time == time(8, 0)


@pytest.mark.asyncio
async def test_reschedule_meal_raises_for_unknown_plan() -> None:
    plan_repo = InMemoryDietPlanRepository()

    with pytest.raises(DietPlanNotFoundError):
        await RescheduleMealUseCase(plan_repo).execute(
            RescheduleMealCommand(
                user_id=uuid4(),
                plan_id=uuid4(),
                day_number=1,
                meal_name="Oatmeal",
                new_time=time(8, 0),
            )
        )


@pytest.mark.asyncio
async def test_reschedule_meal_raises_for_non_owner() -> None:
    plan_repo = InMemoryDietPlanRepository()
    owner_id = uuid4()
    created = await _generate_plan(plan_repo, InMemoryNutritionProfileRepository(), owner_id)

    with pytest.raises(DietPlanNotFoundError):
        await RescheduleMealUseCase(plan_repo).execute(
            RescheduleMealCommand(
                user_id=uuid4(),
                plan_id=UUID(created.plan_id),
                day_number=1,
                meal_name="Oatmeal",
                new_time=time(8, 0),
            )
        )


@pytest.mark.asyncio
async def test_reschedule_meal_raises_for_unknown_meal() -> None:
    plan_repo = InMemoryDietPlanRepository()
    user_id = uuid4()
    created = await _generate_plan(plan_repo, InMemoryNutritionProfileRepository(), user_id)

    with pytest.raises(MealNotFoundError):
        await RescheduleMealUseCase(plan_repo).execute(
            RescheduleMealCommand(
                user_id=user_id,
                plan_id=UUID(created.plan_id),
                day_number=1,
                meal_name="Nonexistent",
                new_time=time(8, 0),
            )
        )
