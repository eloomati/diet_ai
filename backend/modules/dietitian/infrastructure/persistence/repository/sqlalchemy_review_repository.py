from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.modules.dietitian.domain.entities.review import Review
from backend.modules.dietitian.domain.repositories.review_repository import ReviewRepository
from backend.modules.dietitian.infrastructure.mappers.review_mapper import ReviewMapper
from backend.modules.dietitian.infrastructure.persistence.models.review_model import ReviewModel


class SqlAlchemyReviewRepository(ReviewRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_reviewer_and_dietitian(
        self, reviewer_id: UUID, dietitian_id: UUID
    ) -> Review | None:
        stmt = select(ReviewModel).where(
            ReviewModel.reviewer_id == reviewer_id,
            ReviewModel.dietitian_id == dietitian_id,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return ReviewMapper.to_domain(model) if model else None

    async def list_by_dietitian_id(self, dietitian_id: UUID) -> list[Review]:
        stmt = (
            select(ReviewModel)
            .where(ReviewModel.dietitian_id == dietitian_id)
            .order_by(ReviewModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [ReviewMapper.to_domain(model) for model in result.scalars().all()]

    async def rating_summary_by_dietitian_id(self, dietitian_id: UUID) -> tuple[float | None, int]:
        stmt = select(func.avg(ReviewModel.rating), func.count(ReviewModel.id)).where(
            ReviewModel.dietitian_id == dietitian_id
        )
        result = await self._session.execute(stmt)
        average, count = result.one()
        return (float(average) if average is not None else None, count)

    async def save(self, review: Review) -> None:
        existing = await self._session.get(ReviewModel, review.id)

        if existing is None:
            model = ReviewMapper.to_model(review)
            self._session.add(model)
        else:
            # Only `rating`/`comment`/`updated_at` ever change after creation
            # (via `update_content()`) — listed explicitly per the Etap 0
            # lesson, not assumed.
            existing.rating = review.rating
            existing.comment = review.comment
            existing.updated_at = review.updated_at

        await self._session.flush()
