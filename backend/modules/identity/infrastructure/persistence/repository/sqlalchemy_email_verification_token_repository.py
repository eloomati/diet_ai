from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.modules.identity.domain.entities.email_verification_token import (
    EmailVerificationToken,
)
from backend.modules.identity.domain.repositories.email_verification_token_repository import (
    EmailVerificationTokenRepository,
)
from backend.modules.identity.infrastructure.persistence.models.email_verification_token_model import (
    EmailVerificationTokenModel,
)


class SqlAlchemyEmailVerificationTokenRepository(EmailVerificationTokenRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, token: EmailVerificationToken) -> None:
        model = await self._session.get(EmailVerificationTokenModel, token.id)
        if model is None:
            model = EmailVerificationTokenModel(
                id=token.id,
                user_id=token.user_id,
                token_hash=token.token_hash,
                expires_at=token.expires_at,
                used=token.used,
                created_at=token.created_at,
            )
            self._session.add(model)
        else:
            model.used = token.used
        await self._session.flush()

    async def get_by_token_hash(self, token_hash: str) -> EmailVerificationToken | None:
        stmt = select(EmailVerificationTokenModel).where(
            EmailVerificationTokenModel.token_hash == token_hash
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None

        return EmailVerificationToken(
            id=model.id,
            user_id=model.user_id,
            token_hash=model.token_hash,
            expires_at=model.expires_at,
            used=model.used,
            created_at=model.created_at,
        )
