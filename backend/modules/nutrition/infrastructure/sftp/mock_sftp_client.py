from backend.modules.nutrition.application.ports.sftp_client import SftpClient


class MockSftpClient(SftpClient):
    """Deterministic dev/test provider — in-memory, no network calls.

    Constructed fresh per use (see sftp_client_factory.py), so it does NOT persist
    uploads across requests the way the real SFTP server does — it exists so the
    app can boot and be exercised without a live SFTP connection, not to replicate
    the "archive and re-download later" behavior that's the whole point of this
    feature. Tests that need that persistence use a single shared instance
    directly (see tests/fakes.py) instead of going through this factory."""

    def __init__(self) -> None:
        self.files: dict[str, bytes] = {}

    async def upload(self, remote_filename: str, content: bytes) -> None:
        self.files[remote_filename] = content

    async def download(self, remote_filename: str) -> bytes:
        if remote_filename not in self.files:
            raise FileNotFoundError(remote_filename)
        return self.files[remote_filename]
