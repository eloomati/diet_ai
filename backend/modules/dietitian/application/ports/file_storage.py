from abc import ABC, abstractmethod


class FileStorage(ABC):
    @abstractmethod
    async def save(self, filename: str, content: bytes) -> str:
        """Persists the file and returns a URL clients can GET it from."""
        raise NotImplementedError
