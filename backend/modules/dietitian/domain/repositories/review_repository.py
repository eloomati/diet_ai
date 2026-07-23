from abc import ABC, abstractmethod
from uuid import UUID

from backend.modules.dietitian.domain.entities.review import Review


class ReviewRepository(ABC):
    @abstractmethod
    async def get_by_reviewer_and_dietitian(
        self, reviewer_id: UUID, dietitian_id: UUID
    ) -> Review | None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_dietitian_id(self, dietitian_id: UUID) -> list[Review]:
        raise NotImplementedError

    @abstractmethod
    async def rating_summary_by_dietitian_id(self, dietitian_id: UUID) -> tuple[float | None, int]:
        """Returns (average_rating, review_count) — average is None when count is 0."""
        raise NotImplementedError

    @abstractmethod
    async def save(self, review: Review) -> None:
        raise NotImplementedError
