from uuid import UUID, uuid4

import pytest

from backend.modules.ai.tests.fakes import FakeLLMProvider
from backend.modules.nutrition.application import (
    CreateNutritionProfileCommand,
    CreateNutritionProfileUseCase,
    DietPlanNotFoundError,
    GenerateDietPlanCommand,
    GenerateDietPlanUseCase,
    GetDietPlanQuery,
    GetDietPlanUseCase,
    ListDietPlansQuery,
    ListDietPlansUseCase,
)
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


async def _generate_plan(plan_repo, profile_repo, user_id, duration_days: int):
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
async def test_list_diet_plans_returns_only_own_plans() -> None:
    plan_repo = InMemoryDietPlanRepository()
    user_a = uuid4()
    user_b = uuid4()
    await _generate_plan(plan_repo, InMemoryNutritionProfileRepository(), user_a, 2)
    await _generate_plan(plan_repo, InMemoryNutritionProfileRepository(), user_b, 3)

    result = await ListDietPlansUseCase(plan_repo).execute(ListDietPlansQuery(user_id=user_a))

    assert len(result) == 1
    assert result[0].duration_days == 2


@pytest.mark.asyncio
async def test_get_diet_plan_returns_full_plan() -> None:
    plan_repo = InMemoryDietPlanRepository()
    user_id = uuid4()
    created = await _generate_plan(plan_repo, InMemoryNutritionProfileRepository(), user_id, 3)

    result = await GetDietPlanUseCase(plan_repo).execute(
        GetDietPlanQuery(user_id=user_id, plan_id=UUID(created.plan_id))
    )

    assert result.plan_id == created.plan_id
    assert len(result.days) == 3


@pytest.mark.asyncio
async def test_get_diet_plan_raises_for_unknown_plan() -> None:
    plan_repo = InMemoryDietPlanRepository()

    with pytest.raises(DietPlanNotFoundError):
        await GetDietPlanUseCase(plan_repo).execute(GetDietPlanQuery(user_id=uuid4(), plan_id=uuid4()))


@pytest.mark.asyncio
async def test_get_diet_plan_raises_for_non_owner() -> None:
    plan_repo = InMemoryDietPlanRepository()
    owner_id = uuid4()
    created = await _generate_plan(plan_repo, InMemoryNutritionProfileRepository(), owner_id, 1)

    with pytest.raises(DietPlanNotFoundError):
        await GetDietPlanUseCase(plan_repo).execute(
            GetDietPlanQuery(user_id=uuid4(), plan_id=UUID(created.plan_id))
        )
