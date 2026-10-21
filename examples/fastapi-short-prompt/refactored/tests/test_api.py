import sqlite3

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test.db"))
    from app.main import app

    with TestClient(app) as c:
        yield c


def signup_and_login(client, username="alice", password="password123"):
    assert client.post("/auth/signup", json={"username": username, "password": password}).status_code == 201
    r = client.post("/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_signup_duplicate_and_validation(client):
    assert client.post("/auth/signup", json={"username": "bob", "password": "password123"}).status_code == 201
    assert client.post("/auth/signup", json={"username": "BOB", "password": "password123"}).status_code == 409
    assert client.post("/auth/signup", json={"username": "x", "password": "password123"}).status_code == 422
    assert client.post("/auth/signup", json={"username": "carol", "password": "short"}).status_code == 422


def test_signup_does_not_leak_password_hash(client):
    body = client.post("/auth/signup", json={"username": "bob", "password": "password123"}).json()
    assert set(body) == {"id", "username", "created_at"}


def test_login_failures(client):
    signup_and_login(client)
    assert client.post("/auth/login", json={"username": "alice", "password": "wrongpass"}).status_code == 401
    assert client.post("/auth/login", json={"username": "nobody", "password": "password123"}).status_code == 401


def test_me_and_logout(client):
    headers = signup_and_login(client)
    r = client.get("/auth/me", headers=headers)
    assert r.status_code == 200 and r.json()["username"] == "alice"

    assert client.post("/auth/logout", headers=headers).status_code == 204
    assert client.get("/auth/me", headers=headers).status_code == 401


def test_auth_required(client):
    assert client.get("/auth/me").status_code == 401
    assert client.get("/auth/me", headers={"Authorization": "Bearer bogus"}).status_code == 401
    assert client.post("/posts", json={"title": "t", "content": "c"}).status_code == 401


def test_post_crud(client):
    headers = signup_and_login(client)

    r = client.post("/posts", json={"title": "Hello", "content": "World"}, headers=headers)
    assert r.status_code == 201
    post = r.json()
    assert post["title"] == "Hello" and post["author_username"] == "alice"

    assert client.get(f"/posts/{post['id']}").json()["content"] == "World"

    r = client.patch(f"/posts/{post['id']}", json={"title": "Hi"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["title"] == "Hi" and r.json()["content"] == "World"

    assert client.patch(f"/posts/{post['id']}", json={}, headers=headers).status_code == 422

    assert client.delete(f"/posts/{post['id']}", headers=headers).status_code == 204
    assert client.get(f"/posts/{post['id']}").status_code == 404
    assert client.delete(f"/posts/{post['id']}", headers=headers).status_code == 404


def test_only_author_can_modify(client):
    alice = signup_and_login(client, "alice")
    bob = signup_and_login(client, "bob")
    post_id = client.post("/posts", json={"title": "A", "content": "B"}, headers=alice).json()["id"]

    assert client.patch(f"/posts/{post_id}", json={"title": "X"}, headers=bob).status_code == 403
    assert client.delete(f"/posts/{post_id}", headers=bob).status_code == 403
    assert client.get(f"/posts/{post_id}").json()["title"] == "A"


def test_list_pagination_and_filter(client):
    alice = signup_and_login(client, "alice")
    bob = signup_and_login(client, "bob")
    for i in range(5):
        client.post("/posts", json={"title": f"a{i}", "content": "c"}, headers=alice)
    client.post("/posts", json={"title": "b0", "content": "c"}, headers=bob)

    r = client.get("/posts", params={"limit": 2, "offset": 0}).json()
    assert r["total"] == 6 and [p["title"] for p in r["items"]] == ["b0", "a4"]

    alice_id = client.get("/auth/me", headers=alice).json()["id"]
    r = client.get("/posts", params={"author_id": alice_id}).json()
    assert r["total"] == 5 and all(p["author_username"] == "alice" for p in r["items"])

    assert client.get("/posts", params={"limit": 0}).status_code == 422


class FailingCommitConnection(sqlite3.Connection):
    def commit(self):
        raise sqlite3.OperationalError("database is locked")


def test_failed_commit_is_not_reported_as_success(client, monkeypatch):
    headers = signup_and_login(client)
    real_connect = sqlite3.connect
    failing_client = TestClient(client.app, raise_server_exceptions=False)

    with monkeypatch.context() as m:
        m.setattr(
            sqlite3, "connect", lambda *a, **kw: real_connect(*a, factory=FailingCommitConnection, **kw)
        )
        r = failing_client.post("/posts", json={"title": "t", "content": "c"}, headers=headers)

    assert r.status_code == 500
    assert client.get("/posts").json()["total"] == 0
