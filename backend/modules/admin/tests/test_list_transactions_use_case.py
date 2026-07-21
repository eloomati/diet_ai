from uuid import uuid4

import pytest

from backend.modules.admin.application.use_cases.list_transactions_use_case import (
    ListTransactionsUseCase,
)
from backend.modules.transactions.domain.entities.transaction import Transaction
from backend.modules.transactions.domain.value_objects.offer_type import OfferType
from backend.modules.transactions.tests.fakes import InMemoryTransactionRepository


@pytest.mark.asyncio
async def test_list_all_returns_every_transaction() -> None:
    repo = InMemoryTransactionRepository()
    a = Transaction.create(user_id=uuid4(), dietitian_id=uuid4(), offer_type=OfferType.PLAN_REVIEW)
    b = Transaction.create(
        user_id=uuid4(), dietitian_id=uuid4(), offer_type=OfferType.INDIVIDUAL_PLAN
    )
    await repo.save(a)
    await repo.save(b)
    use_case = ListTransactionsUseCase(repo)

    results = await use_case.execute()

    assert {r.id for r in results} == {a.id, b.id}


@pytest.mark.asyncio
async def test_list_all_returns_empty_list_when_none() -> None:
    repo = InMemoryTransactionRepository()
    use_case = ListTransactionsUseCase(repo)

    assert await use_case.execute() == []
