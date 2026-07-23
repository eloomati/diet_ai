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

    Named explicitly (`db-test`, `mongo-test`) rather than bringing up the whole compose
    file — `kafka-test` also lives there, but only one test needs a real broker, so it's
    started on demand by `kafka_test_broker` below instead of taxing every test run.
    """
    _compose("up", "-d", "--wait", "db-test", "mongo-test")
    try:
        subprocess.run(
            ["alembic", "-c", "backend/alembic.ini", "upgrade", "head"],
            check=True,
            cwd=ROOT_DIR,
            env={**os.environ, "DATABASE_URL": TEST_MIGRATION_URL},
        )
        yield
    finally:
        # Tears down the whole compose project — including kafka-test, if the
        # session ever started it.
        _compose("down", "-v")


@pytest.fixture(scope="session")
def kafka_test_broker() -> None:
    """Starts the real single-node Kafka broker, only for the one test that
    needs it. No teardown of its own — `test_database`'s session-scoped
    `finally` above already tears down the entire compose project."""
    _compose("up", "-d", "--wait", "kafka-test")


@pytest.fixture(scope="session")
def redis_test_broker() -> None:
    """Starts the real Redis broker, only for the rate-limiting integration
    test that needs it. No teardown of its own — same reasoning as
    `kafka_test_broker` above."""
    _compose("up", "-d", "--wait", "redis-test")
