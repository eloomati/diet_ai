from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.modules.transactions.domain.entities.transaction import Transaction
from backend.modules.transactions.domain.repositories.transaction_repository import (
    TransactionRepository,
)
from backend.modules.transactions.infrastructure.mappers.transaction_mapper import (
    TransactionMapper,
)
from backend.modules.transactions.infrastructure.persistence.models.transaction_model import (
    TransactionModel,
)


class SqlAlchemyTransactionRepository(TransactionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, transaction_id: UUID) -> Transaction | None:
        model = await self._session.get(TransactionModel, transaction_id)
        return TransactionMapper.to_domain(model) if model else None

    async def list_by_user_id(self, user_id: UUID) -> list[Transaction]:
        stmt = (
            select(TransactionModel)
            .where(TransactionModel.user_id == user_id)
            .order_by(TransactionModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [TransactionMapper.to_domain(model) for model in result.scalars().all()]

    async def list_by_dietitian_id(self, dietitian_id: UUID) -> list[Transaction]:
        stmt = (
            select(TransactionModel)
            .where(TransactionModel.dietitian_id == dietitian_id)
            .order_by(TransactionModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [TransactionMapper.to_domain(model) for model in result.scalars().all()]

    async def list_all(self, limit: int | None = None, offset: int = 0) -> list[Transaction]:
        stmt = (
            select(TransactionModel)
            .order_by(TransactionModel.created_at.desc())
            .offset(offset)
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self._session.execute(stmt)
        return [TransactionMapper.to_domain(model) for model in result.scalars().all()]

    async def count_all(self) -> int:
        stmt = select(func.count()).select_from(TransactionModel)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def save(self, transaction: Transaction) -> None:
        existing = await self._session.get(TransactionModel, transaction.id)

        if existing is None:
            model = TransactionMapper.to_model(transaction)
            self._session.add(model)
        else:
            # `status`/`paid_at` are the only fields any domain method ever
            # changes after creation (mark_paid()/mark_unpaid()) — everything
            # else is set once at create() and never mutated. Listed
            # explicitly rather than assumed, per the Etap 0 lesson: a
            # partial-update list that silently drops a field that *does*
            # change is exactly how that bug happened (there, `role`).
            existing.status = transaction.status.value
            existing.paid_at = transaction.paid_at

        await self._session.flush()
