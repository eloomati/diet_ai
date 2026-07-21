from uuid import UUID

from backend.modules.dietitian.domain.entities.dietitian_application import DietitianApplication
from backend.modules.dietitian.domain.entities.dietitian_profile import DietitianProfile
from backend.modules.dietitian.domain.entities.review import Review


class InMemoryDietitianApplicationRepository:
    def __init__(self) -> None:
        self._by_id: dict[UUID, DietitianApplication] = {}

    async def get_by_id(self, application_id: UUID) -> DietitianApplication | None:
        return self._by_id.get(application_id)

    async def get_by_user_id(self, user_id: UUID) -> DietitianApplication | None:
        for application in self._by_id.values():
            if application.user_id == user_id:
                return application
        return None

    async def save(self, application: DietitianApplication) -> None:
        self._by_id[application.id] = application

    async def list_all(self, status=None) -> list[DietitianApplication]:
        applications = list(self._by_id.values())
        if status is not None:
            applications = [a for a in applications if a.status == status]
        return sorted(applications, key=lambda a: a.created_at)


class InMemoryDietitianProfileRepository:
    def __init__(self) -> None:
        self._by_id: dict[UUID, DietitianProfile] = {}

    async def get_by_user_id(self, user_id: UUID) -> DietitianProfile | None:
        for profile in self._by_id.values():
            if profile.user_id == user_id:
                return profile
        return None

    async def list_all(self) -> list[DietitianProfile]:
        return sorted(self._by_id.values(), key=lambda p: p.created_at, reverse=True)

    async def save(self, profile: DietitianProfile) -> None:
        self._by_id[profile.id] = profile


class InMemoryReviewRepository:
    def __init__(self) -> None:
        self._by_id: dict[UUID, Review] = {}

    async def get_by_reviewer_and_dietitian(
        self, reviewer_id: UUID, dietitian_id: UUID
    ) -> Review | None:
        for review in self._by_id.values():
            if review.reviewer_id == reviewer_id and review.dietitian_id == dietitian_id:
                return review
        return None

    async def list_by_dietitian_id(self, dietitian_id: UUID) -> list[Review]:
        reviews = [r for r in self._by_id.values() if r.dietitian_id == dietitian_id]
        return sorted(reviews, key=lambda r: r.created_at, reverse=True)

    async def rating_summary_by_dietitian_id(self, dietitian_id: UUID) -> tuple[float | None, int]:
        reviews = [r for r in self._by_id.values() if r.dietitian_id == dietitian_id]
        if not reviews:
            return (None, 0)
        return (sum(r.rating for r in reviews) / len(reviews), len(reviews))

    async def save(self, review: Review) -> None:
        self._by_id[review.id] = review


class FakeFileStorage:
    """Records saved files in memory instead of touching disk — the local-disk
    adapter itself is exercised separately, not through use-case tests."""

    def __init__(self) -> None:
        self.saved: list[tuple[str, bytes]] = []

    async def save(self, filename: str, content: bytes) -> str:
        self.saved.append((filename, content))
        return f"/static/dietitian-photos/fake-{len(self.saved)}.jpg"
