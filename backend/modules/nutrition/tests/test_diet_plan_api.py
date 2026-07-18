import uuid
from datetime import date, timedelta

from fastapi.testclient import TestClient


def unique_email(prefix: str) -> str:
    return f"{prefix}.{uuid.uuid4().hex[:10]}@example.com"


def _register_and_login(client: TestClient, prefix: str) -> str:
    email = unique_email(prefix)
    client.post("/api/v1/auth/register", json={"email": email, "password": "StrongPass123"})
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "StrongPass123"})
    return login.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


_PROFILE_PAYLOAD = {
    "age": 29,
    "height_cm": 187,
    "weight_kg": 80,
    "activity_level": "HIGH",
    "goal": "MUSCLE_GAIN",
    "diet_type": "VEGETARIAN",
}


def test_generate_diet_plan_without_profile_returns_404(client: TestClient) -> None:
    token = _register_and_login(client, "dietplan.noprofile")

    response = client.post(
        "/api/v1/diet-plans/generate",
        json={"duration_days": 3},
        headers=_auth_headers(token),
    )

    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"


def test_generate_diet_plan_returns_201(client: TestClient) -> None:
    token = _register_and_login(client, "dietplan.create")
    client.post("/api/v1/profile", json=_PROFILE_PAYLOAD, headers=_auth_headers(token))

    response = client.post(
        "/api/v1/diet-plans/generate",
        json={"duration_days": 3, "requirements": ["high protein breakfasts"]},
        headers=_auth_headers(token),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["duration_days"] == 3
    assert len(body["days"]) == 3
    assert body["goal"] == "MUSCLE_GAIN"
    assert body["diet_type"] == "VEGETARIAN"
    assert body["requirements"] == ["high protein breakfasts"]
    assert body["days"][0]["meals"][0]["name"]


def test_generate_diet_plan_requires_authentication(client: TestClient) -> None:
    response = client.post("/api/v1/diet-plans/generate", json={"duration_days": 3})

    assert response.status_code == 401


def test_generate_diet_plan_rejects_out_of_range_duration(client: TestClient) -> None:
    token = _register_and_login(client, "dietplan.badduration")
    client.post("/api/v1/profile", json=_PROFILE_PAYLOAD, headers=_auth_headers(token))

    response = client.post(
        "/api/v1/diet-plans/generate",
        json={"duration_days": 15},
        headers=_auth_headers(token),
    )

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_list_diet_plans_returns_only_own_plans(client: TestClient) -> None:
    token_a = _register_and_login(client, "dietplan.lista")
    token_b = _register_and_login(client, "dietplan.listb")
    client.post("/api/v1/profile", json=_PROFILE_PAYLOAD, headers=_auth_headers(token_a))
    client.post("/api/v1/profile", json=_PROFILE_PAYLOAD, headers=_auth_headers(token_b))
    client.post(
        "/api/v1/diet-plans/generate", json={"duration_days": 1}, headers=_auth_headers(token_a)
    )

    response_a = client.get("/api/v1/diet-plans", headers=_auth_headers(token_a))
    response_b = client.get("/api/v1/diet-plans", headers=_auth_headers(token_b))

    assert response_a.status_code == 200
    assert len(response_a.json()) == 1
    assert response_b.status_code == 200
    assert response_b.json() == []


def test_list_diet_plans_without_date_filters_returns_everything(client: TestClient) -> None:
    token = _register_and_login(client, "dietplan.nofilter")
    client.post("/api/v1/profile", json=_PROFILE_PAYLOAD, headers=_auth_headers(token))
    client.post(
        "/api/v1/diet-plans/generate", json={"duration_days": 1}, headers=_auth_headers(token)
    )

    response = client.get("/api/v1/diet-plans", headers=_auth_headers(token))

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_list_diet_plans_from_in_the_future_excludes_todays_plan(client: TestClient) -> None:
    token = _register_and_login(client, "dietplan.futurefrom")
    client.post("/api/v1/profile", json=_PROFILE_PAYLOAD, headers=_auth_headers(token))
    client.post(
        "/api/v1/diet-plans/generate", json={"duration_days": 1}, headers=_auth_headers(token)
    )
    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    response = client.get(
        "/api/v1/diet-plans", params={"from": tomorrow}, headers=_auth_headers(token)
    )

    assert response.status_code == 200
    assert response.json() == []


def test_list_diet_plans_from_today_includes_todays_plan(client: TestClient) -> None:
    token = _register_and_login(client, "dietplan.fromtoday")
    client.post("/api/v1/profile", json=_PROFILE_PAYLOAD, headers=_auth_headers(token))
    client.post(
        "/api/v1/diet-plans/generate", json={"duration_days": 1}, headers=_auth_headers(token)
    )
    today = date.today().isoformat()

    response = client.get("/api/v1/diet-plans", params={"from": today}, headers=_auth_headers(token))

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_list_diet_plans_to_in_the_past_excludes_todays_plan(client: TestClient) -> None:
    token = _register_and_login(client, "dietplan.pastto")
    client.post("/api/v1/profile", json=_PROFILE_PAYLOAD, headers=_auth_headers(token))
    client.post(
        "/api/v1/diet-plans/generate", json={"duration_days": 1}, headers=_auth_headers(token)
    )
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    response = client.get("/api/v1/diet-plans", params={"to": yesterday}, headers=_auth_headers(token))

    assert response.status_code == 200
    assert response.json() == []


def test_list_diet_plans_to_today_includes_todays_plan(client: TestClient) -> None:
    token = _register_and_login(client, "dietplan.totoday")
    client.post("/api/v1/profile", json=_PROFILE_PAYLOAD, headers=_auth_headers(token))
    client.post(
        "/api/v1/diet-plans/generate", json={"duration_days": 1}, headers=_auth_headers(token)
    )
    today = date.today().isoformat()

    response = client.get("/api/v1/diet-plans", params={"to": today}, headers=_auth_headers(token))

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_list_diet_plans_from_after_to_returns_400(client: TestClient) -> None:
    token = _register_and_login(client, "dietplan.badrange")
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    today = date.today().isoformat()

    response = client.get(
        "/api/v1/diet-plans",
        params={"from": tomorrow, "to": today},
        headers=_auth_headers(token),
    )

    assert response.status_code == 400
    assert response.json()["code"] == "BAD_REQUEST"


def test_get_diet_plan_returns_full_plan(client: TestClient) -> None:
    token = _register_and_login(client, "dietplan.get")
    client.post("/api/v1/profile", json=_PROFILE_PAYLOAD, headers=_auth_headers(token))
    created = client.post(
        "/api/v1/diet-plans/generate", json={"duration_days": 2}, headers=_auth_headers(token)
    ).json()

    response = client.get(f"/api/v1/diet-plans/{created['plan_id']}", headers=_auth_headers(token))

    assert response.status_code == 200
    assert response.json()["plan_id"] == created["plan_id"]
    assert len(response.json()["days"]) == 2


def test_get_diet_plan_unknown_id_returns_404(client: TestClient) -> None:
    token = _register_and_login(client, "dietplan.unknown")

    response = client.get(
        "/api/v1/diet-plans/00000000-0000-0000-0000-000000000000", headers=_auth_headers(token)
    )

    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"


def test_get_diet_plan_from_other_user_returns_404(client: TestClient) -> None:
    owner_token = _register_and_login(client, "dietplan.owner")
    other_token = _register_and_login(client, "dietplan.other")
    client.post("/api/v1/profile", json=_PROFILE_PAYLOAD, headers=_auth_headers(owner_token))
    created = client.post(
        "/api/v1/diet-plans/generate", json={"duration_days": 1}, headers=_auth_headers(owner_token)
    ).json()

    response = client.get(
        f"/api/v1/diet-plans/{created['plan_id']}", headers=_auth_headers(other_token)
    )

    assert response.status_code == 404


def test_reschedule_meal_updates_only_that_meal(client: TestClient) -> None:
    token = _register_and_login(client, "dietplan.reschedule")
    client.post("/api/v1/profile", json=_PROFILE_PAYLOAD, headers=_auth_headers(token))
    created = client.post(
        "/api/v1/diet-plans/generate", json={"duration_days": 2}, headers=_auth_headers(token)
    ).json()

    response = client.patch(
        f"/api/v1/diet-plans/{created['plan_id']}/meals",
        json={"day_number": 1, "meal_name": "Mock meal", "new_time": "08:00:00"},
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["days"][0]["meals"][0]["time"] == "08:00"
    assert body["days"][1]["meals"][0]["time"] is None

    refetched = client.get(f"/api/v1/diet-plans/{created['plan_id']}", headers=_auth_headers(token))
    assert refetched.json()["days"][0]["meals"][0]["time"] == "08:00"
    assert refetched.json()["days"][1]["meals"][0]["time"] is None


def test_reschedule_meal_on_unknown_plan_returns_404(client: TestClient) -> None:
    token = _register_and_login(client, "dietplan.reschedule.unknown")

    response = client.patch(
        "/api/v1/diet-plans/00000000-0000-0000-0000-000000000000/meals",
        json={"day_number": 1, "meal_name": "Mock meal", "new_time": "08:00:00"},
        headers=_auth_headers(token),
    )

    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"


def test_reschedule_meal_on_other_users_plan_returns_404(client: TestClient) -> None:
    owner_token = _register_and_login(client, "dietplan.reschedule.owner")
    other_token = _register_and_login(client, "dietplan.reschedule.other")
    client.post("/api/v1/profile", json=_PROFILE_PAYLOAD, headers=_auth_headers(owner_token))
    created = client.post(
        "/api/v1/diet-plans/generate", json={"duration_days": 1}, headers=_auth_headers(owner_token)
    ).json()

    response = client.patch(
        f"/api/v1/diet-plans/{created['plan_id']}/meals",
        json={"day_number": 1, "meal_name": "Mock meal", "new_time": "08:00:00"},
        headers=_auth_headers(other_token),
    )

    assert response.status_code == 404


def test_reschedule_unknown_meal_returns_400(client: TestClient) -> None:
    token = _register_and_login(client, "dietplan.reschedule.badmeal")
    client.post("/api/v1/profile", json=_PROFILE_PAYLOAD, headers=_auth_headers(token))
    created = client.post(
        "/api/v1/diet-plans/generate", json={"duration_days": 1}, headers=_auth_headers(token)
    ).json()

    response = client.patch(
        f"/api/v1/diet-plans/{created['plan_id']}/meals",
        json={"day_number": 1, "meal_name": "Nonexistent", "new_time": "08:00:00"},
        headers=_auth_headers(token),
    )

    assert response.status_code == 400
    assert response.json()["code"] == "BAD_REQUEST"
