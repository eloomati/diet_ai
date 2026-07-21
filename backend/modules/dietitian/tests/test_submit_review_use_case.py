from uuid import uuid4

import pytest

from backend.modules.dietitian.application.dto.review_dto import SubmitReviewCommand
from backend.modules.dietitian.application.use_cases.exceptions import DietitianNotFoundError
from backend.modules.dietitian.application.use_cases.submit_review_use_case import (
    SubmitReviewUseCase,
)
from backend.modules.dietitian.domain.exceptions.dietitian_domain_errors import (
    InvalidReviewError,
    SelfReviewError,
)
from backend.modules.dietitian.tests.fakes import InMemoryReviewRepository
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
async def test_submit_review_creates_a_new_review() -> None:
    user_repo = InMemoryUserRepository()
    review_repo = InMemoryReviewRepository()
    dietitian = await _make_dietitian(user_repo, "dietitian1@example.com")
    use_case = SubmitReviewUseCase(review_repo, user_repo)
    reviewer_id = uuid4()

    result = await use_case.execute(
        SubmitReviewCommand(
            reviewer_id=reviewer_id, dietitian_id=dietitian.id, rating=9, comment="Very helpful."
        )
    )

    assert result.rating == 9
    assert result.comment == "Very helpful."
    assert result.dietitian_id == dietitian.id
    assert result.reviewer_id == reviewer_id


@pytest.mark.asyncio
async def test_submit_review_updates_an_existing_review_for_the_same_pair() -> None:
    user_repo = InMemoryUserRepository()
    review_repo = InMemoryReviewRepository()
    dietitian = await _make_dietitian(user_repo, "dietitian2@example.com")
    use_case = SubmitReviewUseCase(review_repo, user_repo)
    reviewer_id = uuid4()
    await use_case.execute(
        SubmitReviewCommand(
            reviewer_id=reviewer_id, dietitian_id=dietitian.id, rating=5, comment="It was okay."
        )
    )

    result = await use_case.execute(
        SubmitReviewCommand(
            reviewer_id=reviewer_id,
            dietitian_id=dietitian.id,
            rating=10,
            comment="Changed my mind, excellent.",
        )
    )

    all_reviews = await review_repo.list_by_dietitian_id(dietitian.id)
    assert len(all_reviews) == 1
    assert result.rating == 10
    assert result.comment == "Changed my mind, excellent."


@pytest.mark.asyncio
async def test_submit_review_raises_when_dietitian_id_unknown() -> None:
    user_repo = InMemoryUserRepository()
    review_repo = InMemoryReviewRepository()
    use_case = SubmitReviewUseCase(review_repo, user_repo)

    with pytest.raises(DietitianNotFoundError):
        await use_case.execute(
            SubmitReviewCommand(
                reviewer_id=uuid4(), dietitian_id=uuid4(), rating=7, comment="N/A"
            )
        )


@pytest.mark.asyncio
async def test_submit_review_raises_when_target_is_not_a_dietitian() -> None:
    user_repo = InMemoryUserRepository()
    review_repo = InMemoryReviewRepository()
    plain_user = User.create(email=Email("plain2@example.com"), password_hash=_password_hash())
    await user_repo.save(plain_user)
    use_case = SubmitReviewUseCase(review_repo, user_repo)

    with pytest.raises(DietitianNotFoundError):
        await use_case.execute(
            SubmitReviewCommand(
                reviewer_id=uuid4(), dietitian_id=plain_user.id, rating=7, comment="N/A"
            )
        )


@pytest.mark.asyncio
async def test_submit_review_rejects_reviewing_yourself() -> None:
    user_repo = InMemoryUserRepository()
    review_repo = InMemoryReviewRepository()
    dietitian = await _make_dietitian(user_repo, "dietitian3@example.com")
    use_case = SubmitReviewUseCase(review_repo, user_repo)

    with pytest.raises(SelfReviewError):
        await use_case.execute(
            SubmitReviewCommand(
                reviewer_id=dietitian.id,
                dietitian_id=dietitian.id,
                rating=10,
                comment="Self-praise.",
            )
        )


@pytest.mark.asyncio
async def test_submit_review_rejects_invalid_rating() -> None:
    user_repo = InMemoryUserRepository()
    review_repo = InMemoryReviewRepository()
    dietitian = await _make_dietitian(user_repo, "dietitian4@example.com")
    use_case = SubmitReviewUseCase(review_repo, user_repo)

    with pytest.raises(InvalidReviewError):
        await use_case.execute(
            SubmitReviewCommand(
                reviewer_id=uuid4(), dietitian_id=dietitian.id, rating=0, comment="Bad rating."
            )
        )
