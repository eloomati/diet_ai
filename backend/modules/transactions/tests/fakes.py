from uuid import UUID

from backend.modules.transactions.domain.entities.transaction import Transaction


class InMemoryTransactionRepository:
    def __init__(self) -> None:
        self._by_id: dict[UUID, Transaction] = {}

    async def get_by_id(self, transaction_id: UUID) -> Transaction | None:
        return self._by_id.get(transaction_id)

    async def list_by_user_id(self, user_id: UUID) -> list[Transaction]:
        transactions = [t for t in self._by_id.values() if t.user_id == user_id]
        return sorted(transactions, key=lambda t: t.created_at, reverse=True)

    async def list_by_dietitian_id(self, dietitian_id: UUID) -> list[Transaction]:
        transactions = [t for t in self._by_id.values() if t.dietitian_id == dietitian_id]
        return sorted(transactions, key=lambda t: t.created_at, reverse=True)

    async def list_all(self) -> list[Transaction]:
        return sorted(self._by_id.values(), key=lambda t: t.created_at, reverse=True)

    async def save(self, transaction: Transaction) -> None:
        self._by_id[transaction.id] = transaction
