from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.modules.identity.application.ports.refresh_token_repository import (
    RefreshTokenRepository,
)
from backend.modules.identity.domain.entities.refresh_token import RefreshToken
from backend.modules.identity.infrastructure.persistence.models.refresh_token_model import (
    RefreshTokenModel,
)


class SqlAlchemyRefreshTokenRepository(RefreshTokenRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, token: RefreshToken) -> None:
        model = RefreshTokenModel(
            id=token.id,
            user_id=token.user_id,
            token_hash=token.token_hash,
            expires_at=token.expires_at,
            revoked=token.revoked,
            created_at=token.created_at,
        )
        self._session.add(model)
        await self._session.flush()

    async def get_active_by_token_hash(self, token_hash: str) -> RefreshToken | None:
        stmt = select(RefreshTokenModel).where(
            RefreshTokenModel.token_hash == token_hash,
            RefreshTokenModel.revoked.is_(False),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None

        return RefreshToken(
            id=model.id,
            user_id=model.user_id,
            token_hash=model.token_hash,
            expires_at=model.expires_at,
            revoked=model.revoked,
            created_at=model.created_at,
        )

    async def revoke(self, token_id: UUID) -> None:
        model = await self._session.get(RefreshTokenModel, token_id)
        if model:
            model.revoked = True
            await self._session.flush()