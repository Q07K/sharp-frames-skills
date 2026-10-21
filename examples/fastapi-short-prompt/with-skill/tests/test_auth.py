import sqlite3
from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

from tests.conftest import PASSWORD, AuthHeaders


def test_signup_returns_public_user_and_stores_hashed_password(
    client: TestClient, db: sqlite3.Connection
) -> None:
    response = client.post("/auth/signup", json={"username": "alice", "password": PASSWORD})

    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "alice"
    assert set(body) == {"id", "username", "created_at"}
    stored = db.execute("SELECT password_hash FROM users WHERE username = 'alice'").fetchone()
    assert stored["password_hash"] != PASSWORD
    assert stored["password_hash"].startswith("$argon2")


@pytest.mark.parametrize("duplicate_name", ["alice", "ALICE"])
def test_signup_rejects_duplicate_username_case_insensitively(
    client: TestClient, db: sqlite3.Connection, duplicate_name: str
) -> None:
    client.post("/auth/signup", json={"username": "alice", "password": PASSWORD})

    response = client.post("/auth/signup", json={"username": duplicate_name, "password": PASSWORD})

    assert response.status_code == 409
    assert db.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 1


@pytest.mark.parametrize(
    "payload",
    [
        {"username": "ab", "password": PASSWORD},  # username too short
        {"username": "a" * 31, "password": PASSWORD},  # username too long
        {"username": "bad name!", "password": PASSWORD},  # disallowed characters
        {"username": "alice", "password": "short"},  # password too short
        {"username": "alice", "password": "p" * 129},  # password too long
        {"username": "alice"},  # missing password
    ],
)
def test_signup_validates_input(client: TestClient, payload: dict[str, str]) -> None:
    response = client.post("/auth/signup", json=payload)

    assert response.status_code == 422


def test_login_issues_token_usable_for_me(client: TestClient) -> None:
    client.post("/auth/signup", json={"username": "alice", "password": PASSWORD})

    login = client.post("/auth/login", json={"username": "alice", "password": PASSWORD})

    assert login.status_code == 200
    token_body = login.json()
    assert token_body["token_type"] == "bearer"
    assert "expires_at" in token_body
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token_body['access_token']}"})
    assert me.status_code == 200
    assert me.json()["username"] == "alice"


def test_login_stores_only_token_hash(client: TestClient, db: sqlite3.Connection) -> None:
    client.post("/auth/signup", json={"username": "alice", "password": PASSWORD})

    token = client.post("/auth/login", json={"username": "alice", "password": PASSWORD}).json()[
        "access_token"
    ]

    stored_hashes = [row[0] for row in db.execute("SELECT token_hash FROM sessions")]
    assert len(stored_hashes) == 1
    assert token not in stored_hashes


@pytest.mark.parametrize(
    ("username", "password"),
    [("alice", "wrong-password"), ("nobody", PASSWORD)],
)
def test_login_failure_is_indistinguishable(client: TestClient, username: str, password: str) -> None:
    client.post("/auth/signup", json={"username": "alice", "password": PASSWORD})

    response = client.post("/auth/login", json={"username": username, "password": password})

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid username or password"}


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"Authorization": "Bearer not-a-real-token"},
        {"Authorization": "Basic YWxpY2U6cGFzc3dvcmQ="},
    ],
)
def test_me_requires_valid_bearer_token(client: TestClient, headers: dict[str, str]) -> None:
    response = client.get("/auth/me", headers=headers)

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_expired_token_is_rejected(
    client: TestClient,
    db: sqlite3.Connection,
    signup_and_login: Callable[[str], AuthHeaders],
) -> None:
    headers = signup_and_login("alice")
    with db:
        db.execute("UPDATE sessions SET expires_at = '2000-01-01T00:00:00+00:00'")

    response = client.get("/auth/me", headers=headers)

    assert response.status_code == 401


def test_logout_revokes_only_that_token(
    client: TestClient,
    db: sqlite3.Connection,
    signup_and_login: Callable[[str], AuthHeaders],
) -> None:
    first_device = signup_and_login("alice")
    second_login = client.post("/auth/login", json={"username": "alice", "password": PASSWORD})
    second_device = {"Authorization": f"Bearer {second_login.json()['access_token']}"}

    logout = client.post("/auth/logout", headers=first_device)

    assert logout.status_code == 204
    assert client.get("/auth/me", headers=first_device).status_code == 401
    assert client.get("/auth/me", headers=second_device).status_code == 200
    assert db.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 1
