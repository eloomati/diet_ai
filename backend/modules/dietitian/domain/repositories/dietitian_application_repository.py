from abc import ABC, abstractmethod
from uuid import UUID

from backend.modules.dietitian.domain.entities.dietitian_application import DietitianApplication
from backend.modules.dietitian.domain.value_objects.application_status import ApplicationStatus


class DietitianApplicationRepository(ABC):
    @abstractmethod
    async def get_by_id(self, application_id: UUID) -> DietitianApplication | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_user_id(self, user_id: UUID) -> DietitianApplication | None:
        raise NotImplementedError

    @abstractmethod
    async def save(self, application: DietitianApplication) -> None:
        raise NotImplementedError

    @abstractmethod
    async def list_all(
        self, status: ApplicationStatus | None = None
    ) -> list[DietitianApplication]:
        raise NotImplementedError
