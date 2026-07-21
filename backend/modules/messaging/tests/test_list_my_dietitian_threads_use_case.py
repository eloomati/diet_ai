import uuid

import pytest

from backend.modules.identity.domain.entities.user import User
from backend.modules.identity.domain.value_objects.email import Email
from backend.modules.identity.domain.value_objects.password_hash import PasswordHash
from backend.modules.identity.tests.fakes import InMemoryUserRepository
from backend.modules.messaging.application.use_cases.list_my_dietitian_threads_use_case import (
    ListMyDietitianThreadsUseCase,
)
from backend.modules.messaging.domain.entities.dietitian_thread import DietitianThread
from backend.modules.messaging.tests.fakes import InMemoryDietitianThreadRepository


def _password_hash() -> PasswordHash:
    return PasswordHash("$2b$12$" + "a" * 22)


@pytest.mark.asyncio
async def test_resolves_the_other_participants_email_from_the_buyer_side() -> None:
    thread_repo = InMemoryDietitianThreadRepository()
    user_repo = InMemoryUserRepository()
    buyer_id = uuid.uuid4()
    dietitian = User.create(email=Email("dietitian@example.com"), password_hash=_password_hash())
    await user_repo.save(dietitian)
    thread = DietitianThread.create(user_id=buyer_id, dietitian_id=dietitian.id)
    await thread_repo.save(thread)
    use_case = ListMyDietitianThreadsUseCase(thread_repo, user_repo)

    results = await use_case.execute(buyer_id)

    assert len(results) == 1
    assert results[0].other_participant_email == "dietitian@example.com"


@pytest.mark.asyncio
async def test_resolves_the_other_participants_email_from_the_dietitian_side() -> None:
    thread_repo = InMemoryDietitianThreadRepository()
    user_repo = InMemoryUserRepository()
    buyer = User.create(email=Email("buyer@example.com"), password_hash=_password_hash())
    await user_repo.save(buyer)
    dietitian_id = uuid.uuid4()
    thread = DietitianThread.create(user_id=buyer.id, dietitian_id=dietitian_id)
    await thread_repo.save(thread)
    use_case = ListMyDietitianThreadsUseCase(thread_repo, user_repo)

    results = await use_case.execute(dietitian_id)

    assert len(results) == 1
    assert results[0].other_participant_email == "buyer@example.com"


@pytest.mark.asyncio
async def test_returns_empty_list_when_no_threads() -> None:
    use_case = ListMyDietitianThreadsUseCase(
        InMemoryDietitianThreadRepository(), InMemoryUserRepository()
    )

    assert await use_case.execute(uuid.uuid4()) == []
