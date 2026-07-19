import asyncio
import uuid
from pathlib import Path

from backend.modules.dietitian.application.ports.file_storage import FileStorage


class LocalDiskFileStorage(FileStorage):
    """MVP storage per the confirmed design decision (local disk, not
    MinIO/S3) — swapping to object storage later only means writing a new
    `FileStorage` implementation, no call sites change."""

    def __init__(self, base_dir: str, base_url: str) -> None:
        self._base_dir = Path(base_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)
        self._base_url = base_url.rstrip("/")

    async def save(self, filename: str, content: bytes) -> str:
        # Never trust the client-supplied filename beyond its extension —
        # the stored name is always our own uuid, which also rules out path
        # traversal since no attacker-controlled path component reaches disk.
        extension = Path(filename).suffix.lower()
        stored_name = f"{uuid.uuid4().hex}{extension}"
        await asyncio.to_thread((self._base_dir / stored_name).write_bytes, content)
        return f"{self._base_url}/{stored_name}"
