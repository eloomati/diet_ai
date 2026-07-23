import uuid

import pytest

from backend.modules.dietitian.domain.entities.dietitian_profile import DietitianProfile
from backend.modules.dietitian.tests.fakes import InMemoryDietitianProfileRepository
from backend.modules.identity.domain.entities.user import User
from backend.modules.identity.domain.value_objects.display_name import DisplayName
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


def _use_case(
    thread_repo: InMemoryDietitianThreadRepository,
    user_repo: InMemoryUserRepository,
    profile_repo: InMemoryDietitianProfileRepository | None = None,
) -> ListMyDietitianThreadsUseCase:
    return ListMyDietitianThreadsUseCase(
        thread_repo, user_repo, profile_repo or InMemoryDietitianProfileRepository()
    )


@pytest.mark.asyncio
async def test_falls_back_to_email_from_the_buyer_side_when_dietitian_has_no_name_set() -> None:
    thread_repo = InMemoryDietitianThreadRepository()
    user_repo = InMemoryUserRepository()
    buyer_id = uuid.uuid4()
    dietitian = User.create(email=Email("dietitian@example.com"), password_hash=_password_hash())
    await user_repo.save(dietitian)
    thread = DietitianThread.create(user_id=buyer_id, dietitian_id=dietitian.id)
    await thread_repo.save(thread)
    use_case = _use_case(thread_repo, user_repo)

    results = await use_case.execute(buyer_id)

    assert len(results) == 1
    assert results[0].other_participant_name == "dietitian@example.com"


@pytest.mark.asyncio
async def test_falls_back_to_email_from_the_dietitian_side_when_buyer_has_no_name_set() -> None:
    thread_repo = InMemoryDietitianThreadRepository()
    user_repo = InMemoryUserRepository()
    buyer = User.create(email=Email("buyer@example.com"), password_hash=_password_hash())
    await user_repo.save(buyer)
    dietitian_id = uuid.uuid4()
    thread = DietitianThread.create(user_id=buyer.id, dietitian_id=dietitian_id)
    await thread_repo.save(thread)
    use_case = _use_case(thread_repo, user_repo)

    results = await use_case.execute(dietitian_id)

    assert len(results) == 1
    assert results[0].other_participant_name == "buyer@example.com"


@pytest.mark.asyncio
async def test_prefers_the_dietitians_real_name_over_their_display_name_and_email() -> None:
    thread_repo = InMemoryDietitianThreadRepository()
    user_repo = InMemoryUserRepository()
    profile_repo = InMemoryDietitianProfileRepository()
    buyer_id = uuid.uuid4()
    dietitian = User.create(email=Email("dietitian@example.com"), password_hash=_password_hash())
    dietitian.set_display_name(DisplayName("DietNick"))
    await user_repo.save(dietitian)
    profile = DietitianProfile.create(
        user_id=dietitian.id,
        experience="5 years",
        diplomas=(),
        description="Helping clients.",
        first_name="Jan",
        last_name="Kowalski",
    )
    await profile_repo.save(profile)
    thread = DietitianThread.create(user_id=buyer_id, dietitian_id=dietitian.id)
    await thread_repo.save(thread)
    use_case = _use_case(thread_repo, user_repo, profile_repo)

    results = await use_case.execute(buyer_id)

    assert results[0].other_participant_name == "Jan Kowalski"


@pytest.mark.asyncio
async def test_uses_the_buyers_display_name_when_set() -> None:
    thread_repo = InMemoryDietitianThreadRepository()
    user_repo = InMemoryUserRepository()
    buyer = User.create(email=Email("buyer@example.com"), password_hash=_password_hash())
    buyer.set_display_name(DisplayName("BuyerNick"))
    await user_repo.save(buyer)
    dietitian_id = uuid.uuid4()
    thread = DietitianThread.create(user_id=buyer.id, dietitian_id=dietitian_id)
    await thread_repo.save(thread)
    use_case = _use_case(thread_repo, user_repo)

    results = await use_case.execute(dietitian_id)

    assert results[0].other_participant_name == "BuyerNick"


@pytest.mark.asyncio
async def test_returns_empty_list_when_no_threads() -> None:
    use_case = _use_case(InMemoryDietitianThreadRepository(), InMemoryUserRepository())

    assert await use_case.execute(uuid.uuid4()) == []
