from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest
import pytest_asyncio

from backend.modules.nutrition.domain import DietDay, DietGoal, DietPlan, DietType, Meal
from backend.modules.nutrition.infrastructure.documents import DietPlanDocument
from backend.modules.nutrition.infrastructure.repository.mongo_diet_plan_repository import (
    MongoDietPlanRepository,
)
from backend.shared.config import get_settings
from backend.shared.database import close_mongo, init_beanie_documents, init_mongo


@pytest_asyncio.fixture
async def repository() -> AsyncGenerator[MongoDietPlanRepository, None]:
    # Beanie's client is bound to the event loop it's created in — init it here,
    # inside this test's own loop, instead of relying on the app's lifespan
    # (which runs in TestClient's separate portal loop/thread).
    settings = get_settings()
    await init_mongo(settings.mongo_url)
    await init_beanie_documents([DietPlanDocument])
    yield MongoDietPlanRepository()
    await close_mongo()


def _plan(**overrides) -> DietPlan:
    defaults = dict(
        user_id=uuid4(),
        goal=DietGoal.MUSCLE_GAIN,
        diet_type=DietType.VEGETARIAN,
        duration_days=2,
        days=(
            DietDay(day_number=1, meals=(Meal("Oatmeal", 400, 20, 60, 10),)),
            DietDay(day_number=2, meals=(Meal("Salad", 350, 25, 30, 15),)),
        ),
        requirements=("high protein",),
    )
    defaults.update(overrides)
    return DietPlan.create(**defaults)


@pytest.mark.asyncio
async def test_save_and_get_by_id_round_trips(repository: MongoDietPlanRepository) -> None:
    plan = _plan()

    await repository.save(plan)
    fetched = await repository.get_by_id(plan.id)

    assert fetched is not None
    assert fetched.user_id == plan.user_id
    assert fetched.duration_days == 2
    assert len(fetched.days) == 2
    assert fetched.days[0].meals[0].name == "Oatmeal"
    assert fetched.requirements == ("high protein",)


@pytest.mark.asyncio
async def test_get_by_id_returns_none_for_unknown_plan(repository: MongoDietPlanRepository) -> None:
    assert await repository.get_by_id(uuid4()) is None


@pytest.mark.asyncio
async def test_list_by_user_id_returns_only_own_plans_newest_first(
    repository: MongoDietPlanRepository,
) -> None:
    user_a = uuid4()
    user_b = uuid4()
    first = _plan(user_id=user_a, duration_days=1, days=(DietDay(1, (Meal("A", 1, 1, 1, 1),)),))
    second = _plan(user_id=user_a, duration_days=1, days=(DietDay(1, (Meal("B", 1, 1, 1, 1),)),))
    await repository.save(first)
    await repository.save(second)
    await repository.save(_plan(user_id=user_b, duration_days=1, days=(DietDay(1, (Meal("C", 1, 1, 1, 1),)),)))

    plans = await repository.list_by_user_id(user_a)

    assert len(plans) == 2
    assert {p.id for p in plans} == {first.id, second.id}


@pytest.mark.asyncio
async def test_list_by_user_id_returns_empty_for_user_with_no_plans(
    repository: MongoDietPlanRepository,
) -> None:
    assert await repository.list_by_user_id(uuid4()) == []
