import uuid

from fastapi.testclient import TestClient


def unique_email(prefix: str) -> str:
    return f"{prefix}.{uuid.uuid4().hex[:10]}@example.com"


def _register_and_login(client: TestClient, prefix: str) -> str:
    email = unique_email(prefix)
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongPass123", "captcha_token": "test-captcha-token"},
    )
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "StrongPass123"})
    return login.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_create_conversation_returns_201(client: TestClient) -> None:
    token = _register_and_login(client, "convo.create")

    response = client.post(
        "/api/v1/conversations",
        json={"title": "Breakfast ideas", "categories": ["BREAKFAST"]},
        headers=_auth_headers(token),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Breakfast ideas"
    assert body["categories"] == ["BREAKFAST"]
    assert body["status"] == "ACTIVE"


def test_create_conversation_with_multiple_categories_returns_all_of_them(client: TestClient) -> None:
    token = _register_and_login(client, "convo.multicat")

    response = client.post(
        "/api/v1/conversations",
        json={"title": "Cutting + race prep", "categories": ["DIET", "RUNNING"]},
        headers=_auth_headers(token),
    )

    assert response.status_code == 201
    assert response.json()["categories"] == ["DIET", "RUNNING"]


def test_create_conversation_requires_authentication(client: TestClient) -> None:
    response = client.post("/api/v1/conversations", json={"title": "No auth", "categories": ["GENERAL"]})

    assert response.status_code == 401


def test_create_conversation_rejects_invalid_category(client: TestClient) -> None:
    token = _register_and_login(client, "convo.badcat")

    response = client.post(
        "/api/v1/conversations",
        json={"title": "Bad category", "categories": ["NOT_A_CATEGORY"]},
        headers=_auth_headers(token),
    )

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_create_conversation_rejects_empty_category_list(client: TestClient) -> None:
    token = _register_and_login(client, "convo.emptycat")

    response = client.post(
        "/api/v1/conversations",
        json={"title": "No categories", "categories": []},
        headers=_auth_headers(token),
    )

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_list_conversations_returns_only_own(client: TestClient) -> None:
    token_a = _register_and_login(client, "convo.list.a")
    token_b = _register_and_login(client, "convo.list.b")

    client.post(
        "/api/v1/conversations",
        json={"title": "Mine", "categories": ["GENERAL"]},
        headers=_auth_headers(token_a),
    )
    client.post(
        "/api/v1/conversations",
        json={"title": "Theirs", "categories": ["GENERAL"]},
        headers=_auth_headers(token_b),
    )

    response = client.get("/api/v1/conversations", headers=_auth_headers(token_a))

    assert response.status_code == 200
    assert {c["title"] for c in response.json()} == {"Mine"}


def test_send_message_and_get_history(client: TestClient) -> None:
    token = _register_and_login(client, "convo.chat")
    created = client.post(
        "/api/v1/conversations",
        json={"title": "Breakfast ideas", "categories": ["BREAKFAST"]},
        headers=_auth_headers(token),
    ).json()
    conversation_id = created["conversation_id"]

    sent = client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={"content": "What should I eat?"},
        headers=_auth_headers(token),
    )
    assert sent.status_code == 201
    assert sent.json()["assistant_content"]

    history = client.get(f"/api/v1/conversations/{conversation_id}", headers=_auth_headers(token))

    assert history.status_code == 200
    messages = history.json()["messages"]
    assert len(messages) == 2
    assert messages[0]["role"] == "USER"
    assert messages[0]["content"] == "What should I eat?"
    assert messages[1]["role"] == "ASSISTANT"


def test_get_unknown_conversation_returns_404(client: TestClient) -> None:
    token = _register_and_login(client, "convo.unknown")

    response = client.get(
        "/api/v1/conversations/00000000-0000-0000-0000-000000000000",
        headers=_auth_headers(token),
    )

    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"


def test_cannot_access_other_users_conversation(client: TestClient) -> None:
    token_owner = _register_and_login(client, "convo.owner")
    token_other = _register_and_login(client, "convo.other")

    created = client.post(
        "/api/v1/conversations",
        json={"title": "Private", "categories": ["GENERAL"]},
        headers=_auth_headers(token_owner),
    ).json()

    response = client.get(
        f"/api/v1/conversations/{created['conversation_id']}",
        headers=_auth_headers(token_other),
    )

    assert response.status_code == 404


def test_cannot_send_message_to_other_users_conversation(client: TestClient) -> None:
    token_owner = _register_and_login(client, "convo.msgowner")
    token_other = _register_and_login(client, "convo.msgother")

    created = client.post(
        "/api/v1/conversations",
        json={"title": "Private", "categories": ["GENERAL"]},
        headers=_auth_headers(token_owner),
    ).json()

    response = client.post(
        f"/api/v1/conversations/{created['conversation_id']}/messages",
        json={"content": "Sneaky"},
        headers=_auth_headers(token_other),
    )

    assert response.status_code == 404


def test_archive_conversation_returns_200_and_updates_status(client: TestClient) -> None:
    token = _register_and_login(client, "convo.archive")
    created = client.post(
        "/api/v1/conversations",
        json={"title": "To archive", "categories": ["GENERAL"]},
        headers=_auth_headers(token),
    ).json()

    response = client.post(
        f"/api/v1/conversations/{created['conversation_id']}/archive",
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ARCHIVED"


def test_archived_conversation_rejects_new_messages_via_api(client: TestClient) -> None:
    token = _register_and_login(client, "convo.archivedmsg")
    created = client.post(
        "/api/v1/conversations",
        json={"title": "To archive", "categories": ["GENERAL"]},
        headers=_auth_headers(token),
    ).json()
    client.post(f"/api/v1/conversations/{created['conversation_id']}/archive", headers=_auth_headers(token))

    response = client.post(
        f"/api/v1/conversations/{created['conversation_id']}/messages",
        json={"content": "Hi"},
        headers=_auth_headers(token),
    )

    assert response.status_code == 409
    assert response.json()["code"] == "CONFLICT"


def test_cannot_archive_other_users_conversation(client: TestClient) -> None:
    token_owner = _register_and_login(client, "convo.archowner")
    token_other = _register_and_login(client, "convo.archother")
    created = client.post(
        "/api/v1/conversations",
        json={"title": "Private", "categories": ["GENERAL"]},
        headers=_auth_headers(token_owner),
    ).json()

    response = client.post(
        f"/api/v1/conversations/{created['conversation_id']}/archive",
        headers=_auth_headers(token_other),
    )

    assert response.status_code == 404


def test_delete_conversation_returns_204_and_removes_it(client: TestClient) -> None:
    token = _register_and_login(client, "convo.delete")
    created = client.post(
        "/api/v1/conversations",
        json={"title": "To delete", "categories": ["GENERAL"]},
        headers=_auth_headers(token),
    ).json()

    response = client.delete(
        f"/api/v1/conversations/{created['conversation_id']}", headers=_auth_headers(token)
    )
    assert response.status_code == 204

    follow_up = client.get(
        f"/api/v1/conversations/{created['conversation_id']}", headers=_auth_headers(token)
    )
    assert follow_up.status_code == 404


def test_cannot_delete_other_users_conversation(client: TestClient) -> None:
    token_owner = _register_and_login(client, "convo.delowner")
    token_other = _register_and_login(client, "convo.delother")
    created = client.post(
        "/api/v1/conversations",
        json={"title": "Private", "categories": ["GENERAL"]},
        headers=_auth_headers(token_owner),
    ).json()

    response = client.delete(
        f"/api/v1/conversations/{created['conversation_id']}", headers=_auth_headers(token_other)
    )

    assert response.status_code == 404


def test_delete_unknown_conversation_returns_404(client: TestClient) -> None:
    token = _register_and_login(client, "convo.delunknown")

    response = client.delete(
        "/api/v1/conversations/00000000-0000-0000-0000-000000000000",
        headers=_auth_headers(token),
    )

    assert response.status_code == 404
