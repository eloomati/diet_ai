from abc import ABC, abstractmethod
from uuid import UUID

from backend.modules.identity.domain.entities.user import User
from backend.modules.identity.domain.value_objects.email import Email


class UserRepository(ABC):
    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_email(self, email: Email) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def exists_by_email(self, email: Email) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def save(self, user: User) -> None:
        raise NotImplementedError

    @abstractmethod
    async def list_all(self, limit: int | None = None, offset: int = 0) -> list[User]:
        raise NotImplementedError

    @abstractmethod
    async def count_all(self) -> int:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, user_id: UUID) -> None:
        raise NotImplementedError