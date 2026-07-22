import os
import time
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from backend.modules.identity.domain.value_objects.role import Role
from backend.modules.identity.infrastructure.persistence.repository.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from backend.modules.messaging.tests.db_helpers import (
    auth_headers,
    register_and_login,
)
from backend.modules.messaging.tests.db_helpers import test_db_session as open_db_session
from backend.shared.config import get_settings

KAFKA_TEST_BOOTSTRAP_SERVERS = "localhost:9095"
POLL_TIMEOUT_SECONDS = 10
POLL_INTERVAL_SECONDS = 0.5


async def _promote(user_id: str, role: Role) -> None:
    async with open_db_session() as session:
        user_repo = SqlAlchemyUserRepository(session)
        user = await user_repo.get_by_id(UUID(user_id))
        user.change_role(role)
        await user_repo.save(user)
        await session.commit()


def _poll(predicate, timeout: float = POLL_TIMEOUT_SECONDS):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = predicate()
        if result:
            return result
        time.sleep(POLL_INTERVAL_SECONDS)
    pytest.fail("Timed out waiting for the Kafka consumers to process the event.")


@pytest.mark.asyncio
async def test_marking_a_transaction_paid_notifies_and_creates_a_thread_via_real_kafka(
    kafka_test_broker,
) -> None:
    """The one real-broker test for this etap: proves the fan-out this whole
    etap was built around — a single `TransactionPaid` publish reaching both
    independent consumer groups (`notifications`, `messaging`) — which every
    prior stage only ever verified by hand against the dev Docker stack."""
    os.environ["KAFKA_PROVIDER"] = "kafka"
    os.environ["KAFKA_BOOTSTRAP_SERVERS"] = KAFKA_TEST_BOOTSTRAP_SERVERS
    get_settings.cache_clear()
    try:
        from backend.app.main import create_app

        with TestClient(create_app()) as client:
            buyer_token, buyer_id = register_and_login(client, "kafka.buyer")
            dietitian_token, dietitian_id = register_and_login(client, "kafka.dietitian")
            admin_token, admin_id = register_and_login(client, "kafka.admin")
            await _promote(dietitian_id, Role.DIET_USER)
            await _promote(admin_id, Role.ADMIN)

            created = client.post(
                "/api/v1/transactions",
                json={"dietitian_id": dietitian_id, "offer_type": "PLAN_REVIEW"},
                headers=auth_headers(buyer_token),
            )
            assert created.status_code == 201
            transaction_id = created.json()["id"]

            paid = client.post(
                f"/api/v1/admin/transactions/{transaction_id}/mark-paid",
                headers=auth_headers(admin_token),
            )
            assert paid.status_code == 200

            def notification_created():
                response = client.get("/api/v1/notifications", headers=auth_headers(dietitian_token))
                notifications = response.json()
                return next(
                    (n for n in notifications if n["type"] == "TRANSACTION_PAID"), None
                )

            def thread_created():
                response = client.get("/api/v1/messaging/threads", headers=auth_headers(dietitian_token))
                threads = response.json()
                return next((t for t in threads if t["dietitian_id"] == dietitian_id), None)

            notification = _poll(notification_created)
            thread = _poll(thread_created)

            assert notification["reference_id"] == transaction_id
            assert thread["user_id"] == buyer_id
    finally:
        os.environ.pop("KAFKA_PROVIDER", None)
        os.environ.pop("KAFKA_BOOTSTRAP_SERVERS", None)
        get_settings.cache_clear()
