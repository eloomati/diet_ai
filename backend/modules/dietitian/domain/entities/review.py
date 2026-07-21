from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from backend.modules.dietitian.domain.exceptions.dietitian_domain_errors import (
    InvalidReviewError,
    SelfReviewError,
)

MIN_RATING = 1
MAX_RATING = 10


@dataclass(slots=True)
class Review:
    id: UUID
    reviewer_id: UUID
    dietitian_id: UUID
    rating: int
    comment: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def create(
        cls,
        reviewer_id: UUID,
        dietitian_id: UUID,
        rating: int,
        comment: str,
    ) -> "Review":
        if reviewer_id == dietitian_id:
            raise SelfReviewError("A dietitian cannot review themselves.")
        cls._validate(rating, comment)
        now = datetime.now(UTC)
        return cls(
            id=uuid4(),
            reviewer_id=reviewer_id,
            dietitian_id=dietitian_id,
            rating=rating,
            comment=comment,
            created_at=now,
            updated_at=now,
        )

    def update_content(self, rating: int, comment: str) -> None:
        self._validate(rating, comment)
        self.rating = rating
        self.comment = comment
        self.updated_at = datetime.now(UTC)

    @staticmethod
    def _validate(rating: int, comment: str) -> None:
        if not MIN_RATING <= rating <= MAX_RATING:
            raise InvalidReviewError(f"Rating must be between {MIN_RATING} and {MAX_RATING}.")
        if not comment.strip():
            raise InvalidReviewError("Comment cannot be empty.")
