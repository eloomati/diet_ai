import uuid

import pytest

from backend.modules.dietitian.domain import (
    ApplicationAlreadyReviewedError,
    ApplicationStatus,
    DietitianApplication,
    InvalidDietitianApplicationError,
)


def _create(**overrides) -> DietitianApplication:
    defaults = dict(
        user_id=uuid.uuid4(),
        experience="5 years as a clinical dietitian",
        diplomas=("MSc Nutrition, University X",),
        description="I help clients build sustainable eating habits.",
    )
    defaults.update(overrides)
    return DietitianApplication.create(**defaults)


def test_create_defaults_to_pending() -> None:
    application = _create()
    assert application.status == ApplicationStatus.PENDING
    assert application.reviewed_by is None
    assert application.reviewed_at is None


def test_create_rejects_empty_experience() -> None:
    with pytest.raises(InvalidDietitianApplicationError):
        _create(experience="   ")


def test_create_rejects_empty_description() -> None:
    with pytest.raises(InvalidDietitianApplicationError):
        _create(description="")


def test_approve_sets_status_and_reviewer() -> None:
    application = _create()
    reviewer_id = uuid.uuid4()

    application.approve(reviewed_by=reviewer_id)

    assert application.status == ApplicationStatus.APPROVED
    assert application.reviewed_by == reviewer_id
    assert application.reviewed_at is not None


def test_reject_sets_status_and_reviewer() -> None:
    application = _create()
    reviewer_id = uuid.uuid4()

    application.reject(reviewed_by=reviewer_id)

    assert application.status == ApplicationStatus.REJECTED
    assert application.reviewed_by == reviewer_id


def test_cannot_approve_an_already_reviewed_application() -> None:
    application = _create()
    application.approve(reviewed_by=uuid.uuid4())

    with pytest.raises(ApplicationAlreadyReviewedError):
        application.approve(reviewed_by=uuid.uuid4())


def test_cannot_reject_an_already_reviewed_application() -> None:
    application = _create()
    application.reject(reviewed_by=uuid.uuid4())

    with pytest.raises(ApplicationAlreadyReviewedError):
        application.reject(reviewed_by=uuid.uuid4())
