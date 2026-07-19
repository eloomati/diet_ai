from uuid import UUID

from backend.modules.dietitian.domain.entities.dietitian_application import DietitianApplication


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
