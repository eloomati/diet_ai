import asyncio

from fastapi.testclient import TestClient

from backend.modules.messaging.tests.db_helpers import (
    auth_headers,
    create_thread_directly,
    promote_to_dietitian,
    register_and_login,
)


def test_list_my_threads_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/messaging/threads")

    assert response.status_code == 401


def test_list_my_threads_returns_empty_list_when_none(client: TestClient) -> None:
    token, _ = register_and_login(client, "msg.nothread")

    response = client.get("/api/v1/messaging/threads", headers=auth_headers(token))

    assert response.status_code == 200
    assert response.json() == []


def test_list_my_threads_resolves_the_other_participants_name(client: TestClient) -> None:
    buyer_token, buyer_id = register_and_login(client, "msg.buyer")
    _, dietitian_id = register_and_login(client, "msg.dietitian")
    asyncio.run(promote_to_dietitian(dietitian_id))
    asyncio.run(create_thread_directly(buyer_id, dietitian_id))

    response = client.get("/api/v1/messaging/threads", headers=auth_headers(buyer_token))

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["dietitian_id"] == dietitian_id
    # Neither side set a display_name or a real name yet — falls back to email.
    assert "@" in body[0]["other_participant_name"]


def test_send_and_list_messages_round_trip(client: TestClient) -> None:
    buyer_token, buyer_id = register_and_login(client, "msg.sendbuyer")
    dietitian_token, dietitian_id = register_and_login(client, "msg.senddiet")
    asyncio.run(promote_to_dietitian(dietitian_id))
    thread_id = asyncio.run(create_thread_directly(buyer_id, dietitian_id))

    sent = client.post(
        f"/api/v1/messaging/threads/{thread_id}/messages",
        json={"content": "Hi, I have a question about my plan."},
        headers=auth_headers(buyer_token),
    )
    assert sent.status_code == 201
    assert sent.json()["sender"] == "USER"

    reply = client.post(
        f"/api/v1/messaging/threads/{thread_id}/messages",
        json={"content": "Sure, what would you like to know?"},
        headers=auth_headers(dietitian_token),
    )
    assert reply.status_code == 201
    assert reply.json()["sender"] == "DIETITIAN"

    messages = client.get(
        f"/api/v1/messaging/threads/{thread_id}/messages", headers=auth_headers(buyer_token)
    )
    assert messages.status_code == 200
    body = messages.json()
    assert len(body) == 2
    assert body[0]["content"] == "Hi, I have a question about my plan."
    assert body[1]["content"] == "Sure, what would you like to know?"


def test_send_message_accepts_an_optional_diet_plan_id(client: TestClient) -> None:
    buyer_token, buyer_id = register_and_login(client, "msg.planbuyer")
    _, dietitian_id = register_and_login(client, "msg.plandiet")
    asyncio.run(promote_to_dietitian(dietitian_id))
    thread_id = asyncio.run(create_thread_directly(buyer_id, dietitian_id))
    plan_id = "11111111-1111-1111-1111-111111111111"

    response = client.post(
        f"/api/v1/messaging/threads/{thread_id}/messages",
        json={"content": "Here's my plan.", "diet_plan_id": plan_id},
        headers=auth_headers(buyer_token),
    )

    assert response.status_code == 201
    assert response.json()["diet_plan_id"] == plan_id


def test_send_message_returns_404_for_unknown_thread(client: TestClient) -> None:
    token, _ = register_and_login(client, "msg.unknownthread")

    response = client.post(
        "/api/v1/messaging/threads/00000000-0000-0000-0000-000000000000/messages",
        json={"content": "Hi"},
        headers=auth_headers(token),
    )

    assert response.status_code == 404


def test_send_message_returns_403_for_a_non_participant(client: TestClient) -> None:
    buyer_token, buyer_id = register_and_login(client, "msg.gatebuyer")
    _, dietitian_id = register_and_login(client, "msg.gatediet")
    asyncio.run(promote_to_dietitian(dietitian_id))
    thread_id = asyncio.run(create_thread_directly(buyer_id, dietitian_id))
    outsider_token, _ = register_and_login(client, "msg.outsider")

    response = client.post(
        f"/api/v1/messaging/threads/{thread_id}/messages",
        json={"content": "Hi"},
        headers=auth_headers(outsider_token),
    )

    assert response.status_code == 403


def test_send_message_rejects_blank_content(client: TestClient) -> None:
    buyer_token, buyer_id = register_and_login(client, "msg.blankbuyer")
    _, dietitian_id = register_and_login(client, "msg.blankdiet")
    asyncio.run(promote_to_dietitian(dietitian_id))
    thread_id = asyncio.run(create_thread_directly(buyer_id, dietitian_id))

    response = client.post(
        f"/api/v1/messaging/threads/{thread_id}/messages",
        json={"content": "   "},
        headers=auth_headers(buyer_token),
    )

    assert response.status_code == 400
