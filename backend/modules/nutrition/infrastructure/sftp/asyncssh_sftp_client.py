import asyncssh

from backend.modules.nutrition.application.ports.sftp_client import SftpClient


class AsyncSshSftpClient(SftpClient):
    """Real SFTP delivery via asyncssh — consistent with the rest of this stack
    being async end to end (Mongo, Postgres, SMTP)."""

    def __init__(self, host: str, port: int, username: str, password: str, remote_dir: str) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._remote_dir = remote_dir.rstrip("/") or "/"

    async def upload(self, remote_filename: str, content: bytes) -> None:
        # known_hosts=None: acceptable for a local/throwaway dev SFTP target (see
        # docker-compose.yml) — a real external target would need host key pinning.
        async with asyncssh.connect(
            self._host,
            port=self._port,
            username=self._username,
            password=self._password,
            known_hosts=None,
        ) as conn:
            async with conn.start_sftp_client() as sftp:
                await sftp.makedirs(self._remote_dir, exist_ok=True)
                async with sftp.open(f"{self._remote_dir}/{remote_filename}", "wb") as f:
                    await f.write(content)

    async def download(self, remote_filename: str) -> bytes:
        async with asyncssh.connect(
            self._host,
            port=self._port,
            username=self._username,
            password=self._password,
            known_hosts=None,
        ) as conn:
            async with conn.start_sftp_client() as sftp:
                async with sftp.open(f"{self._remote_dir}/{remote_filename}", "rb") as f:
                    return await f.read()
