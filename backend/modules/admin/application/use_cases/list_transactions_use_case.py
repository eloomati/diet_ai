from backend.modules.transactions.application.dto.transaction_dto import TransactionResult
from backend.modules.transactions.domain.repositories.transaction_repository import (
    TransactionRepository,
)


class ListTransactionsUseCase:
    def __init__(self, transaction_repository: TransactionRepository) -> None:
        self._transaction_repository = transaction_repository

    async def execute(self) -> list[TransactionResult]:
        transactions = await self._transaction_repository.list_all()
        return [TransactionResult.from_domain(t) for t in transactions]
