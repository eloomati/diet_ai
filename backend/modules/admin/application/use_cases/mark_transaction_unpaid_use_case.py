from uuid import UUID

from backend.modules.transactions.application.dto.transaction_dto import TransactionResult
from backend.modules.transactions.application.use_cases.exceptions import (
    TransactionNotFoundError,
)
from backend.modules.transactions.domain.repositories.transaction_repository import (
    TransactionRepository,
)


class MarkTransactionUnpaidUseCase:
    def __init__(self, transaction_repository: TransactionRepository) -> None:
        self._transaction_repository = transaction_repository

    async def execute(self, transaction_id: UUID) -> TransactionResult:
        transaction = await self._transaction_repository.get_by_id(transaction_id)
        if transaction is None:
            raise TransactionNotFoundError("Transaction not found.")

        transaction.mark_unpaid()
        await self._transaction_repository.save(transaction)

        return TransactionResult.from_domain(transaction)
