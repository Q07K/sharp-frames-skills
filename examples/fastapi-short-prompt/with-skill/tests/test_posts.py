import sqlite3
from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.conftest import AuthHeaders

SignupAndLogin = Callable[[str], AuthHeaders]


def _create_post(client: TestClient, headers: AuthHeaders, title: str = "Hello") -> dict[str, Any]:
    response = client.post("/posts", json={"title": title, "content": "Body"}, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


def test_author_crud_workflow_persists_each_step(
    client: TestClient, db: sqlite3.Connection, signup_and_login: SignupAndLogin
) -> None:
    alice = signup_and_login("alice")
    alice_id = client.get("/auth/me", headers=alice).json()["id"]

    created = client.post("/posts", json={"title": "  First  ", "content": "Hi"}, headers=alice)
    assert created.status_code == 201
    post = created.json()
    assert post["title"] == "First"
    assert post["author"] == {"id": alice_id, "username": "alice"}

    fetched = client.get(f"/posts/{post['id']}")
    assert fetched.status_code == 200
    assert fetched.json() == post

    updated = client.patch(f"/posts/{post['id']}", json={"content": "Edited"}, headers=alice)
    assert updated.status_code == 200
    assert updated.json()["title"] == "First"
    assert updated.json()["content"] == "Edited"
    assert updated.json()["updated_at"] >= post["updated_at"]
    assert updated.json()["created_at"] == post["created_at"]
    stored = db.execute("SELECT title, content FROM posts WHERE id = ?", (post["id"],)).fetchone()
    assert tuple(stored) == ("First", "Edited")

    deleted = client.delete(f"/posts/{post['id']}", headers=alice)
    assert deleted.status_code == 204
    assert client.get(f"/posts/{post['id']}").status_code == 404
    assert db.execute("SELECT COUNT(*) FROM posts").fetchone()[0] == 0


def test_author_is_taken_from_token_not_request_body(
    client: TestClient, signup_and_login: SignupAndLogin
) -> None:
    alice = signup_and_login("alice")
    bob = signup_and_login("bob")
    bob_id = client.get("/auth/me", headers=bob).json()["id"]

    response = client.post(
        "/posts", json={"title": "t", "content": "c", "author_id": bob_id}, headers=alice
    )

    assert response.status_code == 201
    assert response.json()["author"]["username"] == "alice"


def test_other_user_cannot_modify_or_delete_post(
    client: TestClient, db: sqlite3.Connection, signup_and_login: SignupAndLogin
) -> None:
    alice = signup_and_login("alice")
    bob = signup_and_login("bob")
    post = _create_post(client, alice, title="Alice's")

    patch = client.patch(f"/posts/{post['id']}", json={"title": "Hijacked"}, headers=bob)
    delete = client.delete(f"/posts/{post['id']}", headers=bob)

    assert patch.status_code == 403
    assert delete.status_code == 403
    stored = db.execute("SELECT title FROM posts WHERE id = ?", (post["id"],)).fetchone()
    assert stored["title"] == "Alice's"


@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        ("POST", "/posts", {"title": "t", "content": "c"}),
        ("PATCH", "/posts/{id}", {"title": "t"}),
        ("DELETE", "/posts/{id}", None),
    ],
)
def test_writes_require_authentication(
    client: TestClient,
    db: sqlite3.Connection,
    signup_and_login: SignupAndLogin,
    method: str,
    path: str,
    payload: dict[str, str] | None,
) -> None:
    post = _create_post(client, signup_and_login("alice"))

    response = client.request(method, path.format(id=post["id"]), json=payload)

    assert response.status_code == 401
    assert db.execute("SELECT COUNT(*), MAX(title) FROM posts").fetchone()[:] == (1, "Hello")


def test_logged_out_token_cannot_write(client: TestClient, signup_and_login: SignupAndLogin) -> None:
    alice = signup_and_login("alice")
    client.post("/auth/logout", headers=alice)

    response = client.post("/posts", json={"title": "t", "content": "c"}, headers=alice)

    assert response.status_code == 401


@pytest.mark.parametrize("method", ["GET", "PATCH", "DELETE"])
def test_missing_post_returns_404(
    client: TestClient, signup_and_login: SignupAndLogin, method: str
) -> None:
    alice = signup_and_login("alice")

    response = client.request(
        method, "/posts/999", json={"title": "t"} if method == "PATCH" else None, headers=alice
    )

    assert response.status_code == 404


@pytest.mark.parametrize(
    "payload",
    [
        {"title": "   ", "content": "c"},  # blank title after stripping
        {"title": "t" * 201, "content": "c"},
        {"title": "t", "content": ""},
        {"title": "t", "content": "c" * 10_001},
        {"content": "c"},  # missing title
    ],
)
def test_create_validates_input(
    client: TestClient, signup_and_login: SignupAndLogin, payload: dict[str, str]
) -> None:
    response = client.post("/posts", json=payload, headers=signup_and_login("alice"))

    assert response.status_code == 422


@pytest.mark.parametrize("payload", [{}, {"title": None}, {"content": ""}])
def test_update_validates_input(
    client: TestClient, signup_and_login: SignupAndLogin, payload: dict[str, str | None]
) -> None:
    alice = signup_and_login("alice")
    post = _create_post(client, alice)

    response = client.patch(f"/posts/{post['id']}", json=payload, headers=alice)

    assert response.status_code == 422


def test_list_is_public_newest_first_and_paginated(
    client: TestClient, signup_and_login: SignupAndLogin
) -> None:
    alice = signup_and_login("alice")
    bob = signup_and_login("bob")
    first = _create_post(client, alice, title="one")
    second = _create_post(client, bob, title="two")
    third = _create_post(client, alice, title="three")

    page = client.get("/posts", params={"limit": 2, "offset": 0})
    next_page = client.get("/posts", params={"limit": 2, "offset": 2})

    assert page.status_code == 200
    assert [p["id"] for p in page.json()["items"]] == [third["id"], second["id"]]
    assert page.json()["total"] == 3
    assert page.json()["items"][1]["author"]["username"] == "bob"
    assert [p["id"] for p in next_page.json()["items"]] == [first["id"]]


def test_list_empty(client: TestClient) -> None:
    response = client.get("/posts")

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "limit": 20, "offset": 0}


@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 101}, {"offset": -1}])
def test_list_rejects_out_of_range_pagination(client: TestClient, params: dict[str, int]) -> None:
    assert client.get("/posts", params=params).status_code == 422
