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

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        """Revoke every active refresh token for a user (e.g. after a password reset).

        Concrete method with a default, not @abstractmethod: implemented for real in
        Stage 3 (infrastructure) — same reasoning as LLMProvider.generate_structured_response,
        added ahead of its real implementation without breaking the existing concrete
        repository's instantiation.
        """
        raise NotImplementedError(f"{type(self).__name__} does not support revoke_all_for_user.")