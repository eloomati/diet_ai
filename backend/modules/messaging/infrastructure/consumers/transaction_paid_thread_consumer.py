from uuid import UUID

from backend.modules.messaging.application.use_cases.ensure_dietitian_thread_use_case import (
    EnsureDietitianThreadUseCase,
)
from backend.modules.messaging.infrastructure.persistence.repository.sqlalchemy_dietitian_thread_repository import (
    SqlAlchemyDietitianThreadRepository,
)
from backend.shared.config.settings import Settings
from backend.shared.database.postgres import get_postgres_session
from backend.shared.messaging import run_kafka_consumer_loop


async def _handle_transaction_paid_message(payload: dict) -> None:
    dietitian_id = payload.get("dietitian_id")
    if dietitian_id is None:
        # Same edge case notifications' own consumer skips — no dietitian
        # left to open a thread with.
        return

    async with get_postgres_session() as session:
        repository = SqlAlchemyDietitianThreadRepository(session)
        use_case = EnsureDietitianThreadUseCase(repository)
        await use_case.execute(
            user_id=UUID(payload["user_id"]), dietitian_id=UUID(dietitian_id)
        )
        await session.commit()


async def run_transaction_paid_thread_consumer(settings: Settings) -> None:
    """Background task: consumes the same TransactionPaid events as
    `notifications`' own consumer, on an independent consumer group
    (`kafka_messaging_consumer_group_id`) — get-or-creates the
    `DietitianThread` for the pair. Started only when
    `kafka_provider=kafka` (see main.py's lifespan)."""
    await run_kafka_consumer_loop(
        topics=[settings.kafka_transaction_paid_topic],
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id=settings.kafka_messaging_consumer_group_id,
        handle_message=_handle_transaction_paid_message,
    )
