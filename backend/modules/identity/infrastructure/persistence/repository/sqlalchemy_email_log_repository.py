from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.modules.identity.domain.entities.email_log import EmailDeliveryStatus, EmailLog
from backend.modules.identity.domain.repositories.email_log_repository import EmailLogRepository
from backend.modules.identity.infrastructure.persistence.models.email_log_model import EmailLogModel


class SqlAlchemyEmailLogRepository(EmailLogRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, log: EmailLog) -> None:
        model = await self._session.get(EmailLogModel, log.id)
        if model is None:
            model = EmailLogModel(
                id=log.id,
                to=log.to,
                subject=log.subject,
                purpose=log.purpose,
                status=log.status.value,
                attempts=log.attempts,
                next_retry_at=log.next_retry_at,
                error_message=log.error_message,
                created_at=log.created_at,
            )
            self._session.add(model)
        else:
            model.status = log.status.value
            model.attempts = log.attempts
            model.next_retry_at = log.next_retry_at
            model.error_message = log.error_message
        await self._session.flush()

    async def get_due_for_retry(self, now: datetime, limit: int = 50) -> list[EmailLog]:
        stmt = (
            select(EmailLogModel)
            .where(
                EmailLogModel.status == EmailDeliveryStatus.FAILED.value,
                EmailLogModel.next_retry_at.isnot(None),
                EmailLogModel.next_retry_at <= now,
            )
            .order_by(EmailLogModel.next_retry_at)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [
            EmailLog(
                id=model.id,
                to=model.to,
                subject=model.subject,
                purpose=model.purpose,
                status=EmailDeliveryStatus(model.status),
                attempts=model.attempts,
                next_retry_at=model.next_retry_at,
                error_message=model.error_message,
                created_at=model.created_at,
            )
            for model in models
        ]
