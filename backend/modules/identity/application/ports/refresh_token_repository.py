from abc import ABC, abstractmethod
from uuid import UUID

from backend.modules.identity.domain.entities.refresh_token import RefreshToken


class RefreshTokenRepository(ABC):
    @abstractmethod
    async def save(self, token: RefreshToken) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_active_by_token_hash(self, token_hash: str) -> RefreshToken | None:
        raise NotImplementedError

    @abstractmethod
    async def revoke(self, token_id: UUID) -> None:
        raise NotImplementedError