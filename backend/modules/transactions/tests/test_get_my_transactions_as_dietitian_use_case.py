from uuid import uuid4

import pytest

from backend.modules.transactions.application.use_cases.get_my_transactions_as_dietitian_use_case import (
    GetMyTransactionsAsDietitianUseCase,
)
from backend.modules.transactions.domain.entities.transaction import Transaction
from backend.modules.transactions.domain.value_objects.offer_type import OfferType
from backend.modules.transactions.tests.fakes import InMemoryTransactionRepository


@pytest.mark.asyncio
async def test_returns_only_transactions_for_the_given_dietitian() -> None:
    repo = InMemoryTransactionRepository()
    dietitian_id = uuid4()
    mine = Transaction.create(
        user_id=uuid4(), dietitian_id=dietitian_id, offer_type=OfferType.PLAN_REVIEW
    )
    someone_elses = Transaction.create(
        user_id=uuid4(), dietitian_id=uuid4(), offer_type=OfferType.PLAN_REVIEW
    )
    await repo.save(mine)
    await repo.save(someone_elses)
    use_case = GetMyTransactionsAsDietitianUseCase(repo)

    results = await use_case.execute(dietitian_id)

    assert [r.id for r in results] == [mine.id]


@pytest.mark.asyncio
async def test_returns_empty_list_when_none() -> None:
    repo = InMemoryTransactionRepository()
    use_case = GetMyTransactionsAsDietitianUseCase(repo)

    assert await use_case.execute(uuid4()) == []
