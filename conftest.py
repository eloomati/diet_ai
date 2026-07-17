import os
import subprocess
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).parent
COMPOSE_FILE = ROOT_DIR / "docker-compose.test.yml"
TEST_MIGRATION_URL = "postgresql+psycopg2://postgres:postgres@localhost:5433/diet_ai_test"


def _compose(*args: str) -> None:
    subprocess.run(["docker", "compose", "-f", str(COMPOSE_FILE), *args], check=True)


@pytest.fixture(scope="session", autouse=True)
def test_database() -> None:
    """Spin up throwaway Postgres + Mongo containers for the test run, remove them after.

    Keeps tests off the dev databases (see docker-compose.yml's `db`/`mongo` services) —
    tests write/commit real rows, and reusing the dev DBs left that data behind permanently.
    """
    _compose("up", "-d", "--wait")
    try:
        subprocess.run(
            ["alembic", "-c", "backend/alembic.ini", "upgrade", "head"],
            check=True,
            cwd=ROOT_DIR,
            env={**os.environ, "DATABASE_URL": TEST_MIGRATION_URL},
        )
        yield
    finally:
        _compose("down", "-v")
