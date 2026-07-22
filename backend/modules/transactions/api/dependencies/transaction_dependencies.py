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
from backend.modules.transactions.application.use_cases.get_my_purchases_use_case import (
    GetMyPurchasesUseCase,
)
from backend.modules.transactions.application.use_cases.get_my_transactions_as_dietitian_use_case import (
    GetMyTransactionsAsDietitianUseCase,
)
from backend.modules.transactions.domain.repositories.transaction_repository import (
    TransactionRepository,
)
from backend.modules.transactions.infrastructure.events.kafka_transaction_event_publisher import (
    KafkaTransactionEventPublisher,
)
from backend.modules.transactions.infrastructure.events.no_op_transaction_event_publisher import (
    NoOpTransactionEventPublisher,
)
from backend.modules.transactions.infrastructure.persistence.repository.sqlalchemy_transaction_repository import (
    SqlAlchemyTransactionRepository,
)
from backend.shared.config.settings import Settings, get_settings
from backend.shared.database import get_db_session
from backend.shared.messaging import get_kafka_producer


def get_transaction_repository(
    session: AsyncSession = Depends(get_db_session),
) -> TransactionRepository:
    return SqlAlchemyTransactionRepository(session)


def get_transaction_event_publisher(
    settings: Settings = Depends(get_settings),
) -> TransactionEventPublisher:
    # No per-request state needed — same as get_captcha_verifier elsewhere,
    # safe to build fresh per request regardless. Real Kafka publish only
    # when kafka_provider=kafka (see Settings) — mirrors ai_provider/
    # email_provider/sftp_provider's exact mock/real split.
    if settings.kafka_provider == "kafka":
        return KafkaTransactionEventPublisher(
            producer=get_kafka_producer(), topic=settings.kafka_transaction_paid_topic
        )
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
    user_repository: UserRepository = Depends(get_user_repository_for_transactions),
) -> GetMyTransactionsAsDietitianUseCase:
    return GetMyTransactionsAsDietitianUseCase(transaction_repository, user_repository)


def get_my_purchases_use_case(
    transaction_repository: TransactionRepository = Depends(get_transaction_repository),
) -> GetMyPurchasesUseCase:
    return GetMyPurchasesUseCase(transaction_repository)
