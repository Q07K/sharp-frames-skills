import sqlite3
import tempfile
import time
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from board.app import create_app
from board.config import Settings, parse_ttl

PASSWORD = "correct-horse"


class ApiTestCase(unittest.TestCase):
    ttl = 3600

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        # cleanup은 역순으로 실행되므로 임시 폴더 삭제가 마지막에 일어난다.
        self.addCleanup(tmp.cleanup)
        self.db_path = Path(tmp.name) / "nested" / "board.db"
        self.client = self.make_client()
        self.addCleanup(lambda: self.client.close())

    def make_client(self) -> TestClient:
        return TestClient(create_app(Settings(db_path=self.db_path, session_ttl_seconds=self.ttl)))

    def db(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        self.addCleanup(conn.close)
        return conn

    def register(self, username="alice", password=PASSWORD):
        return self.client.post("/auth/register", json={"username": username, "password": password})

    def login(self, username="alice", password=PASSWORD):
        return self.client.post("/auth/login", json={"username": username, "password": password})

    def auth(self, username="alice") -> dict:
        self.register(username)
        res = self.login(username)
        self.assertEqual(res.status_code, 200, res.text)
        return {"Authorization": f"Bearer {res.json()['access_token']}"}

    def create_post(self, headers, title="Hello", content="World"):
        res = self.client.post("/posts", json={"title": title, "content": content}, headers=headers)
        self.assertEqual(res.status_code, 201, res.text)
        return res.json()

    def snapshot(self):
        conn = self.db()
        return (
            [tuple(r) for r in conn.execute("SELECT * FROM users ORDER BY id")],
            [tuple(r) for r in conn.execute("SELECT * FROM posts ORDER BY id")],
        )

    def assert_401(self, res):
        self.assertEqual(res.status_code, 401, res.text)
        self.assertEqual(res.headers.get("www-authenticate"), "Bearer")


class RegisterTests(ApiTestCase):
    def test_register_success(self):
        res = self.register()
        self.assertEqual(res.status_code, 201)
        body = res.json()
        self.assertEqual(set(body), {"id", "username"})
        self.assertIsInstance(body["id"], int)
        self.assertEqual(body["username"], "alice")

    def test_duplicate_username_is_409(self):
        self.assertEqual(self.register().status_code, 201)
        self.assertEqual(self.register(password="another-pass").status_code, 409)
        self.assertEqual(len(self.snapshot()[0]), 1)

    def test_username_validation(self):
        for name in ["ab", "a" * 33, "bad-name", "space name", "한글이름", "abc\n", "", None, 123]:
            with self.subTest(name=name):
                self.assertEqual(self.register(username=name).status_code, 422)
        for name in ["abc", "a" * 32, "User_01"]:
            with self.subTest(name=name):
                self.assertEqual(self.register(username=name).status_code, 201)

    def test_password_validation(self):
        for i, pw in enumerate(["short77", "x" * 129, None, 12345678]):
            with self.subTest(pw=pw):
                self.assertEqual(self.register(username=f"user{i}", password=pw).status_code, 422)
        self.assertEqual(self.register(username="min8", password="x" * 8).status_code, 201)
        self.assertEqual(self.register(username="max128", password="x" * 128).status_code, 201)
        self.assertEqual(len(self.snapshot()[0]), 2)

    def test_password_stored_as_argon2_and_never_returned(self):
        res = self.register()
        self.assertNotIn(PASSWORD, res.text)
        stored = self.db().execute("SELECT password_hash FROM users").fetchone()[0]
        self.assertTrue(stored.startswith("$argon2"), stored)
        self.assertNotIn(PASSWORD, stored)


class LoginTests(ApiTestCase):
    def test_login_success(self):
        self.register()
        res = self.login()
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(set(body), {"access_token", "token_type", "expires_in"})
        self.assertEqual(body["token_type"], "bearer")
        self.assertEqual(body["expires_in"], self.ttl)
        self.assertGreaterEqual(len(body["access_token"]), 32)

    def test_wrong_credentials_are_401(self):
        self.register()
        self.assertEqual(self.login(password="wrong-password").status_code, 401)
        self.assertEqual(self.login(username="nobody").status_code, 401)

    def test_tokens_are_random_and_stored_as_fingerprint(self):
        self.register()
        t1 = self.login().json()["access_token"]
        t2 = self.login().json()["access_token"]
        self.assertNotEqual(t1, t2)
        rows = self.db().execute("SELECT * FROM sessions").fetchall()
        self.assertEqual(len(rows), 2)
        now = int(time.time())
        for row in rows:
            self.assertNotIn(row["token_fingerprint"], (t1, t2))
            self.assertTrue(now + self.ttl - 5 <= row["expires_at"] <= now + self.ttl + 5)
        dump = "\n".join(self.db().iterdump())
        self.assertNotIn(t1, dump)
        self.assertNotIn(t2, dump)


class CustomTtlTests(ApiTestCase):
    ttl = 120

    def test_expires_in_follows_setting(self):
        self.register()
        self.assertEqual(self.login().json()["expires_in"], 120)


class AuthHeaderTests(ApiTestCase):
    def test_missing_malformed_forged_tokens(self):
        body = {"title": "t", "content": "c"}
        self.assert_401(self.client.post("/posts", json=body))
        for header in ["Bearer", "Bearer ", "Basic abc", "token", "Bearer forged-token"]:
            with self.subTest(header=header):
                self.assert_401(self.client.post("/posts", json=body, headers={"Authorization": header}))
        self.assertEqual(self.snapshot()[1], [])

    def test_expired_token(self):
        headers = self.auth()
        self.db().execute("UPDATE sessions SET expires_at = ?", (int(time.time()) - 1,)).connection.commit()
        self.assert_401(self.client.post("/posts", json={"title": "t", "content": "c"}, headers=headers))

    def test_all_write_endpoints_require_auth(self):
        post = self.create_post(self.auth())
        bad = {"Authorization": "Bearer nope"}
        self.assert_401(self.client.put(f"/posts/{post['id']}", json={"title": "x", "content": "y"}))
        self.assert_401(self.client.put(f"/posts/{post['id']}", json={"title": "x", "content": "y"}, headers=bad))
        self.assert_401(self.client.delete(f"/posts/{post['id']}"))
        self.assert_401(self.client.delete(f"/posts/{post['id']}", headers=bad))
        self.assertEqual(self.client.get(f"/posts/{post['id']}").json(), post)

    def test_lowercase_scheme_accepted(self):
        token = self.auth()["Authorization"].split(" ", 1)[1]
        res = self.client.post("/posts", json={"title": "t", "content": "c"}, headers={"Authorization": f"bearer {token}"})
        self.assertEqual(res.status_code, 201)


class PostCrudTests(ApiTestCase):
    def test_create_and_read(self):
        headers = self.auth()
        post = self.create_post(headers, title="  Title  ", content="\n Body \t")
        self.assertEqual(set(post), {"id", "title", "content", "author_id"})
        self.assertEqual(post["title"], "Title")
        self.assertEqual(post["content"], "Body")
        user_id = self.db().execute("SELECT id FROM users").fetchone()[0]
        self.assertEqual(post["author_id"], user_id)
        self.assertEqual(self.client.get(f"/posts/{post['id']}").json(), post)

    def test_get_missing_post_is_404(self):
        self.assertEqual(self.client.get("/posts/999").status_code, 404)
        self.assertEqual(self.client.get("/posts/0").status_code, 404)
        self.assertEqual(self.client.get(f"/posts/{2**70}").status_code, 404)
        self.assertEqual(self.client.get("/posts/abc").status_code, 422)

    def test_author_id_cannot_be_supplied(self):
        headers = self.auth()
        res = self.client.post("/posts", json={"title": "t", "content": "c", "author_id": 999}, headers=headers)
        self.assertEqual(res.status_code, 422)
        self.assertEqual(self.snapshot()[1], [])

    def test_post_validation(self):
        headers = self.auth()
        cases = [
            {"title": "", "content": "c"},
            {"title": "   ", "content": "c"},
            {"title": "t" * 121, "content": "c"},
            {"title": "t", "content": ""},
            {"title": "t", "content": " \n\t "},
            {"title": "t", "content": "c" * 5001},
            {"title": None, "content": "c"},
            {"title": 1, "content": "c"},
            {"title": "t"},
            {"content": "c"},
            {"title": "t", "content": "c", "extra": 1},
            [],
        ]
        for body in cases:
            with self.subTest(body=body):
                self.assertEqual(self.client.post("/posts", json=body, headers=headers).status_code, 422)
        self.assertEqual(self.snapshot()[1], [])
        post = self.create_post(headers, title=" " + "t" * 120 + " ", content="c" * 5000)
        self.assertEqual(len(post["title"]), 120)

    def test_list_order_and_pagination(self):
        headers = self.auth()
        ids = [self.create_post(headers, title=f"p{i}")["id"] for i in range(25)]
        res = self.client.get("/posts")
        self.assertEqual(res.status_code, 200)
        self.assertEqual([p["id"] for p in res.json()], ids[:20])
        self.assertEqual([p["id"] for p in self.client.get("/posts?limit=5&offset=3").json()], ids[3:8])
        self.assertEqual([p["id"] for p in self.client.get("/posts?limit=100").json()], ids)
        self.assertEqual(self.client.get("/posts?offset=100").json(), [])
        for query in ["limit=0", "limit=101", "limit=-1", "offset=-1", "limit=abc", f"offset={2**64}"]:
            with self.subTest(query=query):
                self.assertEqual(self.client.get(f"/posts?{query}").status_code, 422)

    def test_list_empty(self):
        self.assertEqual(self.client.get("/posts").json(), [])

    def test_update_by_author(self):
        headers = self.auth()
        post = self.create_post(headers)
        res = self.client.put(f"/posts/{post['id']}", json={"title": " New ", "content": " Body2 "}, headers=headers)
        self.assertEqual(res.status_code, 200)
        expected = {**post, "title": "New", "content": "Body2"}
        self.assertEqual(res.json(), expected)
        self.assertEqual(self.client.get(f"/posts/{post['id']}").json(), expected)

    def test_update_requires_full_valid_body(self):
        headers = self.auth()
        post = self.create_post(headers)
        before = self.snapshot()
        for body in [{"title": "only"}, {"title": "", "content": "c"}, {"title": "t", "content": "c", "author_id": 2}]:
            with self.subTest(body=body):
                self.assertEqual(self.client.put(f"/posts/{post['id']}", json=body, headers=headers).status_code, 422)
        self.assertEqual(self.snapshot(), before)

    def test_delete_by_author(self):
        headers = self.auth()
        post = self.create_post(headers)
        res = self.client.delete(f"/posts/{post['id']}", headers=headers)
        self.assertEqual(res.status_code, 204)
        self.assertEqual(res.content, b"")
        self.assertEqual(self.client.get(f"/posts/{post['id']}").status_code, 404)
        self.assertEqual(self.client.delete(f"/posts/{post['id']}", headers=headers).status_code, 404)

    def test_other_user_cannot_modify(self):
        alice = self.auth("alice")
        bob = self.auth("bob")
        post = self.create_post(alice)
        before = self.snapshot()
        res = self.client.put(f"/posts/{post['id']}", json={"title": "x", "content": "y"}, headers=bob)
        self.assertEqual(res.status_code, 403)
        self.assertEqual(self.client.delete(f"/posts/{post['id']}", headers=bob).status_code, 403)
        self.assertEqual(self.snapshot(), before)

    def test_missing_post_modify_is_404(self):
        headers = self.auth()
        before = self.snapshot()
        self.assertEqual(self.client.put("/posts/12345", json={"title": "x", "content": "y"}, headers=headers).status_code, 404)
        self.assertEqual(self.client.delete("/posts/12345", headers=headers).status_code, 404)
        self.assertEqual(self.client.delete(f"/posts/{2**70}", headers=headers).status_code, 404)
        self.assertEqual(self.snapshot(), before)

    def test_ids_are_not_reused_after_delete(self):
        headers = self.auth()
        first = self.create_post(headers)
        self.client.delete(f"/posts/{first['id']}", headers=headers)
        self.assertGreater(self.create_post(headers)["id"], first["id"])


class PersistenceTests(ApiTestCase):
    def test_data_survives_new_app_instance(self):
        headers = self.auth()
        post = self.create_post(headers)
        self.client.close()
        self.client = self.make_client()
        self.assertEqual(self.client.get(f"/posts/{post['id']}").json(), post)
        res = self.client.put(f"/posts/{post['id']}", json={"title": "a", "content": "b"}, headers=headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(self.login().status_code, 200)


class ConfigTests(unittest.TestCase):
    def test_parse_ttl(self):
        self.assertEqual(parse_ttl("60"), 60)
        self.assertEqual(parse_ttl(" 7 "), 7)
        for raw in ["0", "-1", "abc", "1.5", "", "+5", "1_000", "١٢"]:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                parse_ttl(raw)


if __name__ == "__main__":
    unittest.main()
