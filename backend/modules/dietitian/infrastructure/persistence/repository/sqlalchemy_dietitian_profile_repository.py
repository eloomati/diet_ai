from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.modules.dietitian.domain.entities.dietitian_profile import DietitianProfile
from backend.modules.dietitian.domain.repositories.dietitian_profile_repository import (
    DietitianProfileRepository,
)
from backend.modules.dietitian.infrastructure.mappers.dietitian_profile_mapper import (
    DietitianProfileMapper,
)
from backend.modules.dietitian.infrastructure.persistence.models.dietitian_profile_model import (
    DietitianProfileModel,
)


class SqlAlchemyDietitianProfileRepository(DietitianProfileRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_user_id(self, user_id: UUID) -> DietitianProfile | None:
        stmt = select(DietitianProfileModel).where(DietitianProfileModel.user_id == user_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return DietitianProfileMapper.to_domain(model) if model else None

    async def save(self, profile: DietitianProfile) -> None:
        existing = await self._session.get(DietitianProfileModel, profile.id)

        if existing is None:
            model = DietitianProfileMapper.to_model(profile)
            self._session.add(model)
        else:
            existing.experience = profile.experience
            existing.diplomas = list(profile.diplomas)
            existing.description = profile.description
            existing.updated_at = profile.updated_at

        await self._session.flush()
