from uuid import uuid4

import pytest

from backend.modules.identity.domain.entities.user import User
from backend.modules.identity.domain.value_objects.email import Email
from backend.modules.identity.domain.value_objects.password_hash import PasswordHash
from backend.modules.identity.tests.fakes import InMemoryUserRepository
from backend.modules.transactions.application.use_cases.get_my_transactions_as_dietitian_use_case import (
    GetMyTransactionsAsDietitianUseCase,
)
from backend.modules.transactions.domain.entities.transaction import Transaction
from backend.modules.transactions.domain.value_objects.offer_type import OfferType
from backend.modules.transactions.tests.fakes import InMemoryTransactionRepository


def _password_hash() -> PasswordHash:
    return PasswordHash("$2b$12$" + "a" * 22)


@pytest.mark.asyncio
async def test_returns_only_transactions_for_the_given_dietitian() -> None:
    repo = InMemoryTransactionRepository()
    user_repo = InMemoryUserRepository()
    dietitian_id = uuid4()
    mine = Transaction.create(
        user_id=uuid4(), dietitian_id=dietitian_id, offer_type=OfferType.PLAN_REVIEW
    )
    someone_elses = Transaction.create(
        user_id=uuid4(), dietitian_id=uuid4(), offer_type=OfferType.PLAN_REVIEW
    )
    await repo.save(mine)
    await repo.save(someone_elses)
    use_case = GetMyTransactionsAsDietitianUseCase(repo, user_repo)

    results = await use_case.execute(dietitian_id)

    assert [r.id for r in results] == [mine.id]


@pytest.mark.asyncio
async def test_returns_empty_list_when_none() -> None:
    repo = InMemoryTransactionRepository()
    user_repo = InMemoryUserRepository()
    use_case = GetMyTransactionsAsDietitianUseCase(repo, user_repo)

    assert await use_case.execute(uuid4()) == []


@pytest.mark.asyncio
async def test_reveals_buyer_email_once_paid() -> None:
    repo = InMemoryTransactionRepository()
    user_repo = InMemoryUserRepository()
    dietitian_id = uuid4()
    buyer = User.create(email=Email("buyer@example.com"), password_hash=_password_hash())
    await user_repo.save(buyer)
    transaction = Transaction.create(
        user_id=buyer.id, dietitian_id=dietitian_id, offer_type=OfferType.PLAN_REVIEW
    )
    transaction.mark_paid()
    await repo.save(transaction)
    use_case = GetMyTransactionsAsDietitianUseCase(repo, user_repo)

    results = await use_case.execute(dietitian_id)

    assert results[0].buyer_email == "buyer@example.com"


@pytest.mark.asyncio
async def test_does_not_reveal_buyer_email_while_unpaid() -> None:
    repo = InMemoryTransactionRepository()
    user_repo = InMemoryUserRepository()
    dietitian_id = uuid4()
    buyer = User.create(email=Email("buyer2@example.com"), password_hash=_password_hash())
    await user_repo.save(buyer)
    transaction = Transaction.create(
        user_id=buyer.id, dietitian_id=dietitian_id, offer_type=OfferType.PLAN_REVIEW
    )
    await repo.save(transaction)
    use_case = GetMyTransactionsAsDietitianUseCase(repo, user_repo)

    results = await use_case.execute(dietitian_id)

    assert results[0].buyer_email is None
