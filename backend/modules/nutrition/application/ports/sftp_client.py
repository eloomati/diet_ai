from abc import ABC, abstractmethod


class SftpClient(ABC):
    @abstractmethod
    async def upload(self, remote_filename: str, content: bytes) -> None:
        raise NotImplementedError

    @abstractmethod
    async def download(self, remote_filename: str) -> bytes:
        raise NotImplementedError
