from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.modules.identity.domain.repositories.user_repository import UserRepository
from backend.modules.identity.infrastructure.persistence.repository.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from backend.modules.transactions.application.ports.transaction_event_publisher import (
    TransactionEventPublisher,
)
from backend.modules.transactions.application.use_cases.create_transaction_use_case import (
    CreateTransactionUseCase,
)
from backend.modules.transactions.application.use_cases.get_my_transactions_as_dietitian_use_case import (
    GetMyTransactionsAsDietitianUseCase,
)
from backend.modules.transactions.domain.repositories.transaction_repository import (
    TransactionRepository,
)
from backend.modules.transactions.infrastructure.events.no_op_transaction_event_publisher import (
    NoOpTransactionEventPublisher,
)
from backend.modules.transactions.infrastructure.persistence.repository.sqlalchemy_transaction_repository import (
    SqlAlchemyTransactionRepository,
)
from backend.shared.database import get_db_session


def get_transaction_repository(
    session: AsyncSession = Depends(get_db_session),
) -> TransactionRepository:
    return SqlAlchemyTransactionRepository(session)


def get_transaction_event_publisher() -> TransactionEventPublisher:
    # No per-request state needed — same as get_captcha_verifier elsewhere,
    # safe to build fresh per request regardless.
    return NoOpTransactionEventPublisher()


def get_user_repository_for_transactions(
    session: AsyncSession = Depends(get_db_session),
) -> UserRepository:
    return SqlAlchemyUserRepository(session)


def get_create_transaction_use_case(
    transaction_repository: TransactionRepository = Depends(get_transaction_repository),
    user_repository: UserRepository = Depends(get_user_repository_for_transactions),
) -> CreateTransactionUseCase:
    return CreateTransactionUseCase(transaction_repository, user_repository)


def get_my_transactions_as_dietitian_use_case(
    transaction_repository: TransactionRepository = Depends(get_transaction_repository),
) -> GetMyTransactionsAsDietitianUseCase:
    return GetMyTransactionsAsDietitianUseCase(transaction_repository)
