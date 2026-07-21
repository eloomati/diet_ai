from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.modules.messaging.domain.entities.dietitian_thread import DietitianThread
from backend.modules.messaging.domain.repositories.dietitian_thread_repository import (
    DietitianThreadRepository,
)
from backend.modules.messaging.infrastructure.mappers.dietitian_thread_mapper import (
    DietitianThreadMapper,
)
from backend.modules.messaging.infrastructure.persistence.models.dietitian_thread_model import (
    DietitianThreadModel,
)


class SqlAlchemyDietitianThreadRepository(DietitianThreadRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, thread_id: UUID) -> DietitianThread | None:
        model = await self._session.get(DietitianThreadModel, thread_id)
        return DietitianThreadMapper.to_domain(model) if model else None

    async def get_by_participants(
        self, user_id: UUID, dietitian_id: UUID
    ) -> DietitianThread | None:
        stmt = select(DietitianThreadModel).where(
            DietitianThreadModel.user_id == user_id,
            DietitianThreadModel.dietitian_id == dietitian_id,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return DietitianThreadMapper.to_domain(model) if model else None

    async def list_by_participant(self, user_id: UUID) -> list[DietitianThread]:
        stmt = (
            select(DietitianThreadModel)
            .where(
                (DietitianThreadModel.user_id == user_id)
                | (DietitianThreadModel.dietitian_id == user_id)
            )
            .order_by(DietitianThreadModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [DietitianThreadMapper.to_domain(model) for model in result.scalars().all()]

    async def save(self, thread: DietitianThread) -> None:
        existing = await self._session.get(DietitianThreadModel, thread.id)

        if existing is None:
            model = DietitianThreadMapper.to_model(thread)
            self._session.add(model)
        # Nothing on DietitianThread ever changes after creation — no
        # update branch needed (unlike every other repository here).

        await self._session.flush()
