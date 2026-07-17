from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.modules.identity.domain.entities.password_reset_token import PasswordResetToken
from backend.modules.identity.domain.repositories.password_reset_token_repository import (
    PasswordResetTokenRepository,
)
from backend.modules.identity.infrastructure.persistence.models.password_reset_token_model import (
    PasswordResetTokenModel,
)


class SqlAlchemyPasswordResetTokenRepository(PasswordResetTokenRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, token: PasswordResetToken) -> None:
        model = await self._session.get(PasswordResetTokenModel, token.id)
        if model is None:
            model = PasswordResetTokenModel(
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

    async def get_by_token_hash(self, token_hash: str) -> PasswordResetToken | None:
        stmt = select(PasswordResetTokenModel).where(PasswordResetTokenModel.token_hash == token_hash)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None

        return PasswordResetToken(
            id=model.id,
            user_id=model.user_id,
            token_hash=model.token_hash,
            expires_at=model.expires_at,
            used=model.used,
            created_at=model.created_at,
        )
