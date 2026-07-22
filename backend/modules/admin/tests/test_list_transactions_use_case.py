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

    page = await use_case.execute()

    assert {r.id for r in page.items} == {a.id, b.id}
    assert page.total == 2


@pytest.mark.asyncio
async def test_list_all_returns_empty_page_when_none() -> None:
    repo = InMemoryTransactionRepository()
    use_case = ListTransactionsUseCase(repo)

    page = await use_case.execute()

    assert page.items == []
    assert page.total == 0


@pytest.mark.asyncio
async def test_list_applies_limit_and_offset() -> None:
    repo = InMemoryTransactionRepository()
    transactions = [
        Transaction.create(user_id=uuid4(), dietitian_id=uuid4(), offer_type=OfferType.PLAN_REVIEW)
        for _ in range(3)
    ]
    for transaction in transactions:
        await repo.save(transaction)
    use_case = ListTransactionsUseCase(repo)

    page = await use_case.execute(limit=1, offset=1)

    # list_all sorts newest-first (created_at desc), so offset=1 skips the
    # most-recently-created transaction (the last one saved).
    assert [r.id for r in page.items] == [transactions[1].id]
    assert page.total == 3
