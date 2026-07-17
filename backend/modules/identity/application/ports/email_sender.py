from abc import ABC, abstractmethod


class EmailSender(ABC):
    @abstractmethod
    async def send(self, to: str, subject: str, body: str) -> None:
        raise NotImplementedError
