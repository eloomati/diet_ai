from abc import ABC, abstractmethod

from backend.modules.identity.domain.entities.password_reset_token import PasswordResetToken


class PasswordResetTokenRepository(ABC):
    @abstractmethod
    async def save(self, token: PasswordResetToken) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_token_hash(self, token_hash: str) -> PasswordResetToken | None:
        raise NotImplementedError
