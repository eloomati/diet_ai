import uuid

import pytest

from backend.modules.dietitian.domain import InvalidReviewError, Review, SelfReviewError


def _create(**overrides) -> Review:
    defaults = dict(
        reviewer_id=uuid.uuid4(),
        dietitian_id=uuid.uuid4(),
        rating=8,
        comment="Great, practical advice.",
    )
    defaults.update(overrides)
    return Review.create(**defaults)


def test_create_rejects_self_review() -> None:
    same_id = uuid.uuid4()

    with pytest.raises(SelfReviewError):
        _create(reviewer_id=same_id, dietitian_id=same_id)


def test_create_rejects_rating_below_range() -> None:
    with pytest.raises(InvalidReviewError):
        _create(rating=0)


def test_create_rejects_rating_above_range() -> None:
    with pytest.raises(InvalidReviewError):
        _create(rating=11)


def test_create_rejects_empty_comment() -> None:
    with pytest.raises(InvalidReviewError):
        _create(comment="   ")


def test_create_accepts_boundary_ratings() -> None:
    assert _create(rating=1).rating == 1
    assert _create(rating=10).rating == 10


def test_update_content_changes_rating_and_comment() -> None:
    review = _create(rating=5, comment="Fine.")
    original_updated_at = review.updated_at

    review.update_content(rating=9, comment="Actually excellent after a follow-up.")

    assert review.rating == 9
    assert review.comment == "Actually excellent after a follow-up."
    assert review.updated_at >= original_updated_at


def test_update_content_rejects_invalid_rating() -> None:
    review = _create()

    with pytest.raises(InvalidReviewError):
        review.update_content(rating=99, comment="Still fine.")
