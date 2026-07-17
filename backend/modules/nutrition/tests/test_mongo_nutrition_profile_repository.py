from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest
import pytest_asyncio
from pymongo.errors import DuplicateKeyError

from backend.modules.nutrition.domain import ActivityLevel, DietGoal, DietType, NutritionProfile
from backend.modules.nutrition.infrastructure.documents import NutritionProfileDocument
from backend.modules.nutrition.infrastructure.repository.mongo_nutrition_profile_repository import (
    MongoNutritionProfileRepository,
)
from backend.shared.config import get_settings
from backend.shared.database import close_mongo, init_beanie_documents, init_mongo


@pytest_asyncio.fixture
async def repository() -> AsyncGenerator[MongoNutritionProfileRepository, None]:
    # Beanie's client is bound to the event loop it's created in — init it here,
    # inside this test's own loop, instead of relying on the app's lifespan
    # (which runs in TestClient's separate portal loop/thread).
    settings = get_settings()
    await init_mongo(settings.mongo_url)
    await init_beanie_documents([NutritionProfileDocument])
    yield MongoNutritionProfileRepository()
    await close_mongo()


def _profile(**overrides) -> NutritionProfile:
    defaults = dict(
        user_id=uuid4(),
        age=29,
        height_cm=187,
        weight_kg=80,
        activity_level=ActivityLevel.HIGH,
        goal=DietGoal.MUSCLE_GAIN,
        diet_type=DietType.VEGETARIAN,
    )
    defaults.update(overrides)
    return NutritionProfile.create(**defaults)


@pytest.mark.asyncio
async def test_save_and_get_by_user_id_round_trips(repository: MongoNutritionProfileRepository) -> None:
    profile = _profile()

    await repository.save(profile)
    fetched = await repository.get_by_user_id(profile.user_id)

    assert fetched is not None
    assert fetched.user_id == profile.user_id
    assert fetched.age == 29
    assert fetched.activity_level == ActivityLevel.HIGH


@pytest.mark.asyncio
async def test_get_by_user_id_returns_none_for_unknown_user(
    repository: MongoNutritionProfileRepository,
) -> None:
    assert await repository.get_by_user_id(uuid4()) is None


@pytest.mark.asyncio
async def test_save_upserts_existing_profile(repository: MongoNutritionProfileRepository) -> None:
    profile = _profile()
    await repository.save(profile)

    profile.update(weight_kg=82)
    await repository.save(profile)

    fetched = await repository.get_by_user_id(profile.user_id)
    assert fetched.weight_kg == 82


@pytest.mark.asyncio
async def test_unique_index_rejects_second_profile_for_same_user(
    repository: MongoNutritionProfileRepository,
) -> None:
    user_id = uuid4()
    await repository.save(_profile(user_id=user_id))

    # A *different* profile document (different id) for the same user_id must
    # be rejected at the DB level by the unique index, not just the
    # application-layer check in CreateNutritionProfileUseCase.
    with pytest.raises(DuplicateKeyError):
        await repository.save(_profile(user_id=user_id))
