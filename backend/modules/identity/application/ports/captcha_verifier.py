from abc import ABC, abstractmethod


class CaptchaVerifier(ABC):
    @abstractmethod
    async def verify(self, token: str) -> bool:
        raise NotImplementedError
