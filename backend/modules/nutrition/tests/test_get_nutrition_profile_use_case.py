from uuid import uuid4

import pytest

from backend.modules.nutrition.application import (
    CreateNutritionProfileCommand,
    CreateNutritionProfileUseCase,
    GetNutritionProfileQuery,
    GetNutritionProfileUseCase,
    NutritionProfileNotFoundError,
)
from backend.modules.nutrition.tests.fakes import InMemoryNutritionProfileRepository


@pytest.mark.asyncio
async def test_get_nutrition_profile_returns_created_profile() -> None:
    repo = InMemoryNutritionProfileRepository()
    user_id = uuid4()
    await CreateNutritionProfileUseCase(repo).execute(
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

    result = await GetNutritionProfileUseCase(repo).execute(GetNutritionProfileQuery(user_id=user_id))

    assert result.age == 29
    assert result.user_id == str(user_id)


@pytest.mark.asyncio
async def test_get_nutrition_profile_raises_when_missing() -> None:
    repo = InMemoryNutritionProfileRepository()

    with pytest.raises(NutritionProfileNotFoundError):
        await GetNutritionProfileUseCase(repo).execute(GetNutritionProfileQuery(user_id=uuid4()))
