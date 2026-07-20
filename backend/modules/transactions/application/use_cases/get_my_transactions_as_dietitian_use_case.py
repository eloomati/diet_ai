from uuid import UUID

from backend.modules.transactions.application.dto.transaction_dto import TransactionResult
from backend.modules.transactions.domain.repositories.transaction_repository import (
    TransactionRepository,
)


class GetMyTransactionsAsDietitianUseCase:
    def __init__(self, transaction_repository: TransactionRepository) -> None:
        self._transaction_repository = transaction_repository

    async def execute(self, dietitian_id: UUID) -> list[TransactionResult]:
        transactions = await self._transaction_repository.list_by_dietitian_id(dietitian_id)
        return [TransactionResult.from_domain(t) for t in transactions]
