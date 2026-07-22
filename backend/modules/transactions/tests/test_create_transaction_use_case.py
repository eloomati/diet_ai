from uuid import uuid4

import pytest

from backend.modules.identity.domain.entities.user import User
from backend.modules.identity.domain.value_objects.email import Email
from backend.modules.identity.domain.value_objects.password_hash import PasswordHash
from backend.modules.identity.domain.value_objects.role import Role
from backend.modules.identity.tests.fakes import InMemoryUserRepository
from backend.modules.transactions.application.dto.transaction_dto import (
    CreateTransactionCommand,
)
from backend.modules.transactions.application.use_cases.create_transaction_use_case import (
    CreateTransactionUseCase,
)
from backend.modules.transactions.application.use_cases.exceptions import (
    DietitianNotFoundError,
    EmailNotVerifiedError,
)
from backend.modules.transactions.domain.exceptions.transaction_domain_errors import (
    InvalidTransactionError,
)
from backend.modules.transactions.domain.value_objects.offer_type import OfferType
from backend.modules.transactions.domain.value_objects.transaction_status import (
    TransactionStatus,
)
from backend.modules.transactions.tests.fakes import InMemoryTransactionRepository


def _password_hash() -> PasswordHash:
    return PasswordHash("$2b$12$" + "a" * 22)


@pytest.mark.asyncio
async def test_create_transaction_succeeds_for_a_real_dietitian() -> None:
    user_repo = InMemoryUserRepository()
    transaction_repo = InMemoryTransactionRepository()
    dietitian = User.create(email=Email("dietitian@example.com"), password_hash=_password_hash())
    dietitian.change_role(Role.DIET_USER)
    await user_repo.save(dietitian)
    buyer = User.create(email=Email("buyer@example.com"), password_hash=_password_hash())
    buyer.mark_email_verified()
    await user_repo.save(buyer)
    use_case = CreateTransactionUseCase(transaction_repo, user_repo)

    result = await use_case.execute(
        CreateTransactionCommand(
            user_id=buyer.id, dietitian_id=dietitian.id, offer_type=OfferType.PLAN_REVIEW
        )
    )

    assert result.status == TransactionStatus.UNPAID
    assert result.dietitian_id == dietitian.id
    assert result.user_id == buyer.id


@pytest.mark.asyncio
async def test_create_transaction_raises_when_dietitian_id_unknown() -> None:
    user_repo = InMemoryUserRepository()
    transaction_repo = InMemoryTransactionRepository()
    use_case = CreateTransactionUseCase(transaction_repo, user_repo)

    with pytest.raises(DietitianNotFoundError):
        await use_case.execute(
            CreateTransactionCommand(
                user_id=uuid4(), dietitian_id=uuid4(), offer_type=OfferType.PLAN_REVIEW
            )
        )


@pytest.mark.asyncio
async def test_create_transaction_raises_when_target_is_not_a_dietitian() -> None:
    user_repo = InMemoryUserRepository()
    transaction_repo = InMemoryTransactionRepository()
    plain_user = User.create(email=Email("plain@example.com"), password_hash=_password_hash())
    await user_repo.save(plain_user)
    use_case = CreateTransactionUseCase(transaction_repo, user_repo)

    with pytest.raises(DietitianNotFoundError):
        await use_case.execute(
            CreateTransactionCommand(
                user_id=uuid4(), dietitian_id=plain_user.id, offer_type=OfferType.PLAN_REVIEW
            )
        )


@pytest.mark.asyncio
async def test_create_transaction_rejects_buying_your_own_offer() -> None:
    user_repo = InMemoryUserRepository()
    transaction_repo = InMemoryTransactionRepository()
    dietitian = User.create(email=Email("self@example.com"), password_hash=_password_hash())
    dietitian.change_role(Role.DIET_USER)
    dietitian.mark_email_verified()
    await user_repo.save(dietitian)
    use_case = CreateTransactionUseCase(transaction_repo, user_repo)

    with pytest.raises(InvalidTransactionError):
        await use_case.execute(
            CreateTransactionCommand(
                user_id=dietitian.id, dietitian_id=dietitian.id, offer_type=OfferType.PLAN_REVIEW
            )
        )


@pytest.mark.asyncio
async def test_create_transaction_raises_when_buyer_email_not_verified() -> None:
    user_repo = InMemoryUserRepository()
    transaction_repo = InMemoryTransactionRepository()
    dietitian = User.create(email=Email("dietitian2@example.com"), password_hash=_password_hash())
    dietitian.change_role(Role.DIET_USER)
    await user_repo.save(dietitian)
    buyer = User.create(email=Email("unverified@example.com"), password_hash=_password_hash())
    await user_repo.save(buyer)
    use_case = CreateTransactionUseCase(transaction_repo, user_repo)

    with pytest.raises(EmailNotVerifiedError):
        await use_case.execute(
            CreateTransactionCommand(
                user_id=buyer.id, dietitian_id=dietitian.id, offer_type=OfferType.PLAN_REVIEW
            )
        )
