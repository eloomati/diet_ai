from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.modules.dietitian.domain.entities.dietitian_application import DietitianApplication
from backend.modules.dietitian.domain.repositories.dietitian_application_repository import (
    DietitianApplicationRepository,
)
from backend.modules.dietitian.infrastructure.mappers.dietitian_application_mapper import (
    DietitianApplicationMapper,
)
from backend.modules.dietitian.infrastructure.persistence.models.dietitian_application_model import (
    DietitianApplicationModel,
)


class SqlAlchemyDietitianApplicationRepository(DietitianApplicationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, application_id: UUID) -> DietitianApplication | None:
        model = await self._session.get(DietitianApplicationModel, application_id)
        return DietitianApplicationMapper.to_domain(model) if model else None

    async def get_by_user_id(self, user_id: UUID) -> DietitianApplication | None:
        stmt = select(DietitianApplicationModel).where(DietitianApplicationModel.user_id == user_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return DietitianApplicationMapper.to_domain(model) if model else None

    async def save(self, application: DietitianApplication) -> None:
        existing = await self._session.get(DietitianApplicationModel, application.id)

        if existing is None:
            model = DietitianApplicationMapper.to_model(application)
            self._session.add(model)
        else:
            # Every mutable field, not a hand-picked subset — Etap 0 found that
            # exact kind of partial-update list silently drops whichever field
            # isn't listed (there, `role`; here it would have been `status`).
            existing.experience = application.experience
            existing.diplomas = list(application.diplomas)
            existing.description = application.description
            existing.status = application.status.value
            existing.reviewed_by = application.reviewed_by
            existing.reviewed_at = application.reviewed_at
            existing.updated_at = application.updated_at

        await self._session.flush()
