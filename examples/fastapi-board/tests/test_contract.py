"""Run the same public API contract against either implementation."""

import argparse
from contextlib import closing, contextmanager
import importlib.util
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]


def load_factory(variant):
    if variant == "before":
        spec = importlib.util.spec_from_file_location("board_before", ROOT / "before/main.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module.create_app
    sys.path.insert(0, str(ROOT / "after"))
    from board_api.main import create_app
    return create_app


class BoardContract(unittest.TestCase):
    def __init__(self, methodName="runTest", variant="before"):
        super().__init__(methodName)
        self.variant = variant

    def __str__(self):
        return f"{super().__str__()} [{self.variant}]"

    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory()
        self.addCleanup(self.workspace.cleanup)
        self.db_path = str(Path(self.workspace.name) / "board.sqlite3")
        self.factory = load_factory(self.variant)
        self.client = TestClient(self.factory(self.db_path), raise_server_exceptions=False)
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)

    @contextmanager
    def database(self):
        with closing(sqlite3.connect(self.db_path)) as db:
            with db:
                yield db

    def login(self, username="alice"):
        credentials = {"username": username, "password": "test-password-123"}
        registered = self.client.post("/auth/register", json=credentials)
        self.assertEqual(registered.status_code, 201, registered.text)
        self.assertEqual(set(registered.json()), {"id", "username"})
        response = self.client.post("/auth/login", json=credentials)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["token_type"], "bearer")
        self.assertEqual(response.json()["expires_in"], 3600)
        return {"Authorization": "Bearer " + response.json()["access_token"]}

    def create_post(self, headers):
        response = self.client.post("/posts", headers=headers, json={"title": "First post", "content": "Hello"})
        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(set(response.json()), {"id", "title", "content", "author_id"})
        return response.json()

    def test_register_login_and_wrong_password(self):
        headers = self.login()
        duplicate = self.client.post("/auth/register", json={"username": "alice", "password": "another-password"})
        self.assertEqual(duplicate.status_code, 409)
        for username in ("alice", "missing"):
            response = self.client.post("/auth/login", json={"username": username, "password": "wrong-password"})
            self.assertEqual(response.status_code, 401)
        self.create_post(headers)
        with self.database() as db:
            password_hash = db.execute("SELECT password_hash FROM users").fetchone()[0]
            token_hash = db.execute("SELECT token_hash FROM sessions").fetchone()[0]
        self.assertTrue(password_hash.startswith("$argon2"))
        self.assertNotEqual(password_hash, "test-password-123")
        self.assertNotEqual(token_hash, headers["Authorization"].removeprefix("Bearer "))

    def test_author_crud_workflow(self):
        headers = self.login()
        post = self.create_post(headers)
        url = f"/posts/{post['id']}"
        self.assertEqual(self.client.get(url).json(), post)
        self.assertEqual(self.client.get("/posts").json(), [post])
        changed = self.client.put(url, headers=headers, json={"title": "  Updated  ", "content": "New content"})
        self.assertEqual(changed.status_code, 200)
        self.assertEqual(changed.json()["title"], "Updated")
        self.assertEqual(changed.json()["author_id"], post["author_id"])
        self.assertEqual(self.client.get(url).json()["content"], "New content")
        deleted = self.client.delete(url, headers=headers)
        self.assertEqual(deleted.status_code, 204)
        self.assertEqual(deleted.content, b"")
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.get("/posts").json(), [])

    def test_anonymous_writes_are_rejected(self):
        post = self.create_post(self.login())
        url = f"/posts/{post['id']}"
        self.assertEqual(self.client.post("/posts", json={"title": "x", "content": "y"}).status_code, 401)
        self.assertEqual(self.client.put(url, json={"title": "x", "content": "y"}).status_code, 401)
        self.assertEqual(self.client.delete(url).status_code, 401)
        self.assertEqual(self.client.get(url).json(), post)

    def test_other_author_is_denied_without_side_effects(self):
        alice = self.login()
        post = self.create_post(alice)
        bob = self.login("bob")
        url = f"/posts/{post['id']}"
        self.assertEqual(self.client.put(url, headers=bob, json={"title": "stolen", "content": "changed"}).status_code, 403)
        self.assertEqual(self.client.delete(url, headers=bob).status_code, 403)
        self.assertEqual(self.client.get(url).json(), post)
        self.assertEqual(self.client.delete(url, headers=alice).status_code, 204)

    def test_invalid_and_expired_tokens(self):
        headers = self.login()
        post = self.create_post(headers)
        data = {"title": "x", "content": "y"}
        forged = {"Authorization": "Bearer made-up-token"}
        self.assertEqual(self.client.post("/posts", headers=forged, json=data).status_code, 401)
        with self.database() as db:
            db.execute("UPDATE sessions SET expires_at = 0")
        self.assertEqual(self.client.delete(f"/posts/{post['id']}", headers=headers).status_code, 401)
        self.assertEqual(self.client.get(f"/posts/{post['id']}").json(), post)

    def test_input_validation_and_pagination(self):
        headers = self.login()
        for data in ({"title": " ", "content": "x"}, {"title": "x" * 121, "content": "x"},
                     {"title": "x", "content": " "}, {"title": "x", "content": "y", "author_id": 999}):
            self.assertEqual(self.client.post("/posts", headers=headers, json=data).status_code, 422)
        self.assertEqual(self.client.get("/posts").json(), [])
        first = self.create_post(headers)
        second = self.create_post(headers)
        self.assertEqual(self.client.get("/posts?limit=1&offset=1").json(), [second])
        self.assertNotEqual(first["id"], second["id"])
        for query in ("limit=0", "limit=101", "offset=-1"):
            self.assertEqual(self.client.get("/posts?" + query).status_code, 422)

    def test_missing_post_is_not_found(self):
        headers = self.login()
        self.assertEqual(self.client.get("/posts/999").status_code, 404)
        self.assertEqual(self.client.put("/posts/999", headers=headers, json={"title": "x", "content": "y"}).status_code, 404)
        self.assertEqual(self.client.delete("/posts/999", headers=headers).status_code, 404)

    def test_database_survives_app_restart(self):
        headers = self.login()
        post = self.create_post(headers)
        with TestClient(self.factory(self.db_path)) as restarted:
            self.assertEqual(restarted.get(f"/posts/{post['id']}").json(), post)
            self.assertEqual(restarted.delete(f"/posts/{post['id']}", headers=headers).status_code, 204)

    def test_failed_write_does_not_persist_and_retry_works(self):
        headers = self.login()
        with self.database() as db:
            db.execute("CREATE TRIGGER reject_post BEFORE INSERT ON posts BEGIN SELECT RAISE(ABORT, 'test failure'); END")
        response = self.client.post("/posts", headers=headers, json={"title": "x", "content": "y"})
        self.assertEqual(response.status_code, 500)
        self.assertEqual(self.client.get("/posts").json(), [])
        with self.database() as db:
            db.execute("DROP TRIGGER reject_post")
        self.create_post(headers)
        self.assertEqual(len(self.client.get("/posts").json()), 1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant", choices=("before", "after", "both"), default="both")
    args = parser.parse_args()
    variants = ("before", "after") if args.variant == "both" else (args.variant,)
    names = unittest.defaultTestLoader.getTestCaseNames(BoardContract)
    suite = unittest.TestSuite(BoardContract(name, variant) for variant in variants for name in names)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(not result.wasSuccessful())
