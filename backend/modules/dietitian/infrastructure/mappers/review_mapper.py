from backend.modules.dietitian.domain.entities.review import Review
from backend.modules.dietitian.infrastructure.persistence.models.review_model import ReviewModel


class ReviewMapper:
    @staticmethod
    def to_domain(model: ReviewModel) -> Review:
        return Review(
            id=model.id,
            reviewer_id=model.reviewer_id,
            dietitian_id=model.dietitian_id,
            rating=model.rating,
            comment=model.comment,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(review: Review) -> ReviewModel:
        return ReviewModel(
            id=review.id,
            reviewer_id=review.reviewer_id,
            dietitian_id=review.dietitian_id,
            rating=review.rating,
            comment=review.comment,
            created_at=review.created_at,
            updated_at=review.updated_at,
        )
