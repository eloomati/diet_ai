from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from backend.modules.dietitian.domain.entities.review import Review


@dataclass(frozen=True, slots=True)
class SubmitReviewCommand:
    reviewer_id: UUID
    dietitian_id: UUID
    rating: int
    comment: str


@dataclass(frozen=True, slots=True)
class ReviewResult:
    id: UUID
    reviewer_id: UUID
    dietitian_id: UUID
    rating: int
    comment: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, review: Review) -> "ReviewResult":
        return cls(
            id=review.id,
            reviewer_id=review.reviewer_id,
            dietitian_id=review.dietitian_id,
            rating=review.rating,
            comment=review.comment,
            created_at=review.created_at,
            updated_at=review.updated_at,
        )


@dataclass(frozen=True, slots=True)
class PublicReviewResult:
    """A review as shown to the public — deliberately omits the reviewer's identity."""

    rating: int
    comment: str
    created_at: datetime

    @classmethod
    def from_domain(cls, review: Review) -> "PublicReviewResult":
        return cls(rating=review.rating, comment=review.comment, created_at=review.created_at)
