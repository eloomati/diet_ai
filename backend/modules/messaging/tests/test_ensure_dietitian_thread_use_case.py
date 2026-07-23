import uuid

import pytest

from backend.modules.messaging.application.use_cases.ensure_dietitian_thread_use_case import (
    EnsureDietitianThreadUseCase,
)
from backend.modules.messaging.tests.fakes import InMemoryDietitianThreadRepository


@pytest.mark.asyncio
async def test_creates_a_new_thread_when_none_exists() -> None:
    repository = InMemoryDietitianThreadRepository()
    use_case = EnsureDietitianThreadUseCase(repository)
    user_id, dietitian_id = uuid.uuid4(), uuid.uuid4()

    result = await use_case.execute(user_id=user_id, dietitian_id=dietitian_id)

    assert result.user_id == user_id
    assert result.dietitian_id == dietitian_id
    stored = await repository.get_by_participants(user_id, dietitian_id)
    assert stored is not None
    assert stored.id == result.id


@pytest.mark.asyncio
async def test_reuses_the_existing_thread_for_the_same_pair() -> None:
    repository = InMemoryDietitianThreadRepository()
    use_case = EnsureDietitianThreadUseCase(repository)
    user_id, dietitian_id = uuid.uuid4(), uuid.uuid4()

    first = await use_case.execute(user_id=user_id, dietitian_id=dietitian_id)
    second = await use_case.execute(user_id=user_id, dietitian_id=dietitian_id)

    assert first.id == second.id
    assert len(await repository.list_by_participant(user_id)) == 1
