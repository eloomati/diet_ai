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
    reviewer_name: str
    dietitian_id: UUID
    rating: int
    comment: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, review: Review, reviewer_name: str) -> "ReviewResult":
        return cls(
            id=review.id,
            reviewer_id=review.reviewer_id,
            reviewer_name=reviewer_name,
            dietitian_id=review.dietitian_id,
            rating=review.rating,
            comment=review.comment,
            created_at=review.created_at,
            updated_at=review.updated_at,
        )


@dataclass(frozen=True, slots=True)
class PublicReviewResult:
    """A review as shown to the public — used to deliberately omit the
    reviewer's identity entirely (Phase 12); reversed in Phase 13 now that
    a resolved display name is available instead of a raw UUID."""

    reviewer_name: str
    rating: int
    comment: str
    created_at: datetime

    @classmethod
    def from_domain(cls, review: Review, reviewer_name: str) -> "PublicReviewResult":
        return cls(
            reviewer_name=reviewer_name,
            rating=review.rating,
            comment=review.comment,
            created_at=review.created_at,
        )
