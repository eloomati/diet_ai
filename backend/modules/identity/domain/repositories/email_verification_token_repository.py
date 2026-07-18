from abc import ABC, abstractmethod

from backend.modules.identity.domain.entities.email_verification_token import (
    EmailVerificationToken,
)


class EmailVerificationTokenRepository(ABC):
    @abstractmethod
    async def save(self, token: EmailVerificationToken) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_token_hash(self, token_hash: str) -> EmailVerificationToken | None:
        raise NotImplementedError
