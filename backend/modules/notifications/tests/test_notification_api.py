import asyncio

from fastapi.testclient import TestClient

from backend.modules.notifications.tests.db_helpers import (
    auth_headers,
    create_thread_directly,
    promote_to_dietitian,
    register_and_login,
)


def test_list_my_notifications_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/notifications")

    assert response.status_code == 401


def test_list_my_notifications_returns_empty_list_when_none(client: TestClient) -> None:
    token, _ = register_and_login(client, "notif.nothing")

    response = client.get("/api/v1/notifications", headers=auth_headers(token))

    assert response.status_code == 200
    assert response.json() == []


def test_sending_a_message_notifies_the_other_participant(client: TestClient) -> None:
    buyer_token, buyer_id = register_and_login(client, "notif.buyer")
    dietitian_token, dietitian_id = register_and_login(client, "notif.dietitian")
    asyncio.run(promote_to_dietitian(dietitian_id))
    thread_id = asyncio.run(create_thread_directly(buyer_id, dietitian_id))

    sent = client.post(
        f"/api/v1/messaging/threads/{thread_id}/messages",
        json={"content": "Hi, quick question."},
        headers=auth_headers(buyer_token),
    )
    assert sent.status_code == 201

    response = client.get("/api/v1/notifications", headers=auth_headers(dietitian_token))

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["type"] == "NEW_MESSAGE"
    assert body[0]["reference_id"] == thread_id
    assert body[0]["read_at"] is None

    buyer_notifications = client.get("/api/v1/notifications", headers=auth_headers(buyer_token))
    assert buyer_notifications.json() == []


def test_mark_all_notifications_read_clears_unread_notifications(client: TestClient) -> None:
    buyer_token, buyer_id = register_and_login(client, "notif.markbuyer")
    dietitian_token, dietitian_id = register_and_login(client, "notif.markdiet")
    asyncio.run(promote_to_dietitian(dietitian_id))
    thread_id = asyncio.run(create_thread_directly(buyer_id, dietitian_id))
    client.post(
        f"/api/v1/messaging/threads/{thread_id}/messages",
        json={"content": "Hi!"},
        headers=auth_headers(buyer_token),
    )

    mark_read = client.post(
        "/api/v1/notifications/mark-all-read", headers=auth_headers(dietitian_token)
    )

    assert mark_read.status_code == 200
    marked = mark_read.json()
    assert len(marked) == 1
    assert marked[0]["read_at"] is not None

    response = client.get("/api/v1/notifications", headers=auth_headers(dietitian_token))
    assert response.json()[0]["read_at"] is not None
