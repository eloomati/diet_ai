from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.modules.messaging.domain.entities.dietitian_message import DietitianMessage
from backend.modules.messaging.domain.repositories.dietitian_message_repository import (
    DietitianMessageRepository,
)
from backend.modules.messaging.infrastructure.mappers.dietitian_message_mapper import (
    DietitianMessageMapper,
)
from backend.modules.messaging.infrastructure.persistence.models.dietitian_message_model import (
    DietitianMessageModel,
)


class SqlAlchemyDietitianMessageRepository(DietitianMessageRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_thread_id(self, thread_id: UUID) -> list[DietitianMessage]:
        stmt = (
            select(DietitianMessageModel)
            .where(DietitianMessageModel.thread_id == thread_id)
            .order_by(DietitianMessageModel.created_at.asc())
        )
        result = await self._session.execute(stmt)
        return [DietitianMessageMapper.to_domain(model) for model in result.scalars().all()]

    async def save(self, message: DietitianMessage) -> None:
        existing = await self._session.get(DietitianMessageModel, message.id)

        if existing is None:
            model = DietitianMessageMapper.to_model(message)
            self._session.add(model)
        # Messages are immutable once sent — no update branch needed.

        await self._session.flush()
