from uuid import uuid4

import pytest

from backend.modules.dietitian.application.use_cases.list_dietitians_use_case import (
    ListDietitiansUseCase,
)
from backend.modules.dietitian.domain.entities.dietitian_profile import DietitianProfile
from backend.modules.dietitian.domain.entities.review import Review
from backend.modules.dietitian.tests.fakes import (
    InMemoryDietitianProfileRepository,
    InMemoryReviewRepository,
)
from backend.modules.identity.domain.entities.user import User
from backend.modules.identity.domain.value_objects.email import Email
from backend.modules.identity.domain.value_objects.password_hash import PasswordHash
from backend.modules.identity.domain.value_objects.role import Role
from backend.modules.identity.tests.fakes import InMemoryUserRepository


def _password_hash() -> PasswordHash:
    return PasswordHash("$2b$12$" + "a" * 22)


async def _make_dietitian(user_repo: InMemoryUserRepository, email: str) -> User:
    dietitian = User.create(email=Email(email), password_hash=_password_hash())
    dietitian.change_role(Role.DIET_USER)
    await user_repo.save(dietitian)
    return dietitian


@pytest.mark.asyncio
async def test_list_dietitians_includes_active_dietitians_with_rating_summary() -> None:
    user_repo = InMemoryUserRepository()
    profile_repo = InMemoryDietitianProfileRepository()
    review_repo = InMemoryReviewRepository()
    dietitian = await _make_dietitian(user_repo, "listed@example.com")
    profile = DietitianProfile.create(
        user_id=dietitian.id,
        experience="5 years",
        diplomas=("MSc Dietetics",),
        description="Weight management specialist.",
    )
    await profile_repo.save(profile)
    reviewer_id = uuid4()
    await review_repo.save(
        Review.create(reviewer_id=reviewer_id, dietitian_id=dietitian.id, rating=8, comment="Good.")
    )
    use_case = ListDietitiansUseCase(profile_repo, user_repo, review_repo)

    results = await use_case.execute()

    assert len(results) == 1
    assert results[0].user_id == dietitian.id
    assert results[0].name == "listed@example.com"
    assert results[0].average_rating == 8.0
    assert results[0].review_count == 1


@pytest.mark.asyncio
async def test_list_dietitians_prefers_the_dietitians_real_name() -> None:
    user_repo = InMemoryUserRepository()
    profile_repo = InMemoryDietitianProfileRepository()
    review_repo = InMemoryReviewRepository()
    dietitian = await _make_dietitian(user_repo, "named@example.com")
    profile = DietitianProfile.create(
        user_id=dietitian.id,
        experience="5 years",
        diplomas=(),
        description="Description.",
        first_name="Jan",
        last_name="Kowalski",
    )
    await profile_repo.save(profile)
    use_case = ListDietitiansUseCase(profile_repo, user_repo, review_repo)

    results = await use_case.execute()

    assert results[0].name == "Jan Kowalski"


@pytest.mark.asyncio
async def test_list_dietitians_excludes_banned_dietitians() -> None:
    user_repo = InMemoryUserRepository()
    profile_repo = InMemoryDietitianProfileRepository()
    review_repo = InMemoryReviewRepository()
    dietitian = await _make_dietitian(user_repo, "banned@example.com")
    dietitian.block()
    await user_repo.save(dietitian)
    profile = DietitianProfile.create(
        user_id=dietitian.id,
        experience="5 years",
        diplomas=(),
        description="Description.",
    )
    await profile_repo.save(profile)
    use_case = ListDietitiansUseCase(profile_repo, user_repo, review_repo)

    results = await use_case.execute()

    assert results == []


@pytest.mark.asyncio
async def test_list_dietitians_excludes_profiles_whose_role_was_reversed() -> None:
    user_repo = InMemoryUserRepository()
    profile_repo = InMemoryDietitianProfileRepository()
    review_repo = InMemoryReviewRepository()
    dietitian = await _make_dietitian(user_repo, "reversed@example.com")
    profile = DietitianProfile.create(
        user_id=dietitian.id,
        experience="5 years",
        diplomas=(),
        description="Description.",
    )
    await profile_repo.save(profile)
    dietitian.change_role(Role.USER)
    await user_repo.save(dietitian)
    use_case = ListDietitiansUseCase(profile_repo, user_repo, review_repo)

    results = await use_case.execute()

    assert results == []


@pytest.mark.asyncio
async def test_list_dietitians_returns_empty_when_none_exist() -> None:
    use_case = ListDietitiansUseCase(
        InMemoryDietitianProfileRepository(), InMemoryUserRepository(), InMemoryReviewRepository()
    )

    results = await use_case.execute()

    assert results == []
