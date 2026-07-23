from pathlib import Path

import pytest

from backend.modules.dietitian.infrastructure.storage.local_disk_file_storage import (
    LocalDiskFileStorage,
)


@pytest.mark.asyncio
async def test_save_writes_file_and_returns_url(tmp_path: Path) -> None:
    storage = LocalDiskFileStorage(base_dir=str(tmp_path), base_url="/static/dietitian-photos")

    url = await storage.save("my photo.jpg", b"fake-bytes")

    assert url.startswith("/static/dietitian-photos/")
    assert url.endswith(".jpg")
    stored_files = list(tmp_path.iterdir())
    assert len(stored_files) == 1
    assert stored_files[0].read_bytes() == b"fake-bytes"


@pytest.mark.asyncio
async def test_save_ignores_the_client_supplied_filename_beyond_its_extension(tmp_path: Path) -> None:
    storage = LocalDiskFileStorage(base_dir=str(tmp_path), base_url="/static/dietitian-photos")

    url = await storage.save("../../etc/passwd.png", b"fake-bytes")

    stored_files = list(tmp_path.iterdir())
    assert len(stored_files) == 1
    assert stored_files[0].name != "passwd.png"
    assert url == f"/static/dietitian-photos/{stored_files[0].name}"
