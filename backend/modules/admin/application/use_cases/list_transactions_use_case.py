from backend.modules.admin.application.dto.pagination_dto import PageResult
from backend.modules.transactions.application.dto.transaction_dto import TransactionResult
from backend.modules.transactions.domain.repositories.transaction_repository import (
    TransactionRepository,
)


class ListTransactionsUseCase:
    def __init__(self, transaction_repository: TransactionRepository) -> None:
        self._transaction_repository = transaction_repository

    async def execute(
        self, limit: int | None = None, offset: int = 0
    ) -> PageResult[TransactionResult]:
        transactions = await self._transaction_repository.list_all(limit=limit, offset=offset)
        total = await self._transaction_repository.count_all()
        return PageResult(
            items=[TransactionResult.from_domain(t) for t in transactions], total=total
        )
