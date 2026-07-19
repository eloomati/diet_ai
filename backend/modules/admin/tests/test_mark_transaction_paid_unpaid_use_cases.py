from uuid import uuid4

import pytest

from backend.modules.admin.application.use_cases.mark_transaction_paid_use_case import (
    MarkTransactionPaidUseCase,
)
from backend.modules.admin.application.use_cases.mark_transaction_unpaid_use_case import (
    MarkTransactionUnpaidUseCase,
)
from backend.modules.transactions.application.use_cases.exceptions import (
    TransactionNotFoundError,
)
from backend.modules.transactions.domain.entities.transaction import Transaction
from backend.modules.transactions.domain.value_objects.offer_type import OfferType
from backend.modules.transactions.domain.value_objects.transaction_status import (
    TransactionStatus,
)
from backend.modules.transactions.infrastructure.events.no_op_transaction_event_publisher import (
    NoOpTransactionEventPublisher,
)
from backend.modules.transactions.tests.fakes import InMemoryTransactionRepository


def _transaction() -> Transaction:
    return Transaction.create(
        user_id=uuid4(), dietitian_id=uuid4(), offer_type=OfferType.PLAN_REVIEW
    )


@pytest.mark.asyncio
async def test_mark_paid_updates_status_and_publishes_event() -> None:
    repo = InMemoryTransactionRepository()
    transaction = _transaction()
    await repo.save(transaction)
    publisher = NoOpTransactionEventPublisher()
    use_case = MarkTransactionPaidUseCase(repo, publisher)

    result = await use_case.execute(transaction.id)

    assert result.status == TransactionStatus.PAID
    assert result.paid_at is not None
    assert len(publisher.published) == 1
    assert publisher.published[0].id == transaction.id


@pytest.mark.asyncio
async def test_mark_paid_raises_when_transaction_missing() -> None:
    repo = InMemoryTransactionRepository()
    publisher = NoOpTransactionEventPublisher()
    use_case = MarkTransactionPaidUseCase(repo, publisher)

    with pytest.raises(TransactionNotFoundError):
        await use_case.execute(uuid4())

    assert publisher.published == []


@pytest.mark.asyncio
async def test_mark_unpaid_updates_status_without_publishing() -> None:
    repo = InMemoryTransactionRepository()
    transaction = _transaction()
    transaction.mark_paid()
    await repo.save(transaction)
    use_case = MarkTransactionUnpaidUseCase(repo)

    result = await use_case.execute(transaction.id)

    assert result.status == TransactionStatus.UNPAID
    assert result.paid_at is None


@pytest.mark.asyncio
async def test_mark_unpaid_raises_when_transaction_missing() -> None:
    repo = InMemoryTransactionRepository()
    use_case = MarkTransactionUnpaidUseCase(repo)

    with pytest.raises(TransactionNotFoundError):
        await use_case.execute(uuid4())
