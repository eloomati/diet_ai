from abc import ABC, abstractmethod


class TokenService(ABC):
    @abstractmethod
    def create_access_token(self, user_id: str, email: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def create_refresh_token(self, user_id: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def decode_refresh_token(self, token: str) -> dict:
        raise NotImplementedError

    @abstractmethod
    def decode_access_token(self, token: str) -> dict:
        raise NotImplementedError