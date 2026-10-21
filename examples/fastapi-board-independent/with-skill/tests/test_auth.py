import hashlib
import unittest

from tests.support import PASSWORD, ApiTestCase


class RegisterTests(ApiTestCase):
    def test_register_returns_public_user_and_stores_argon2_hash(self) -> None:
        response = self.client.post(
            "/auth/register", json={"username": "alice_1", "password": PASSWORD}
        )

        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(set(body), {"id", "username"})
        self.assertIsInstance(body["id"], int)
        self.assertEqual(body["username"], "alice_1")
        [row] = self.query("SELECT password_hash FROM users")
        self.assertTrue(row["password_hash"].startswith("$argon2"))
        self.assertNotIn(PASSWORD, row["password_hash"])

    def test_duplicate_username_is_409_and_keeps_one_user(self) -> None:
        self.register("alice")

        response = self.client.post(
            "/auth/register", json={"username": "alice", "password": "another-pass"}
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(len(self.query("SELECT id FROM users")), 1)

    def test_username_and_password_boundaries(self) -> None:
        valid = [
            ("abc", "x" * 8),
            ("a" * 32, "x" * 128),
            ("Under_Score_9", "pass word"),
        ]
        for username, password in valid:
            with self.subTest(username=username, password_length=len(password)):
                response = self.client.post(
                    "/auth/register", json={"username": username, "password": password}
                )
                self.assertEqual(response.status_code, 201, response.text)

        invalid = [
            {"username": "ab", "password": "x" * 8},
            {"username": "a" * 33, "password": "x" * 8},
            {"username": "bad-name", "password": "x" * 8},
            {"username": "spa ce", "password": "x" * 8},
            {"username": "한글이름", "password": "x" * 8},
            {"username": "valid_name", "password": "x" * 7},
            {"username": "valid_name", "password": "x" * 129},
            {"username": "valid_name"},
            {"password": "x" * 8},
            {"username": 12345, "password": "x" * 8},
        ]
        for payload in invalid:
            with self.subTest(payload=payload):
                response = self.client.post("/auth/register", json=payload)
                self.assertEqual(response.status_code, 422, response.text)
        self.assertEqual(len(self.query("SELECT id FROM users")), len(valid))


class LoginTests(ApiTestCase):
    session_ttl_seconds = 120

    def test_login_issues_bearer_token_and_stores_only_fingerprint(self) -> None:
        user = self.register("alice")

        response = self.client.post(
            "/auth/login", json={"username": "alice", "password": PASSWORD}
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["token_type"], "bearer")
        self.assertEqual(body["expires_in"], 120)
        token = body["access_token"]
        self.assertGreaterEqual(len(token), 32)
        [session] = self.query("SELECT * FROM sessions")
        self.assertEqual(session["user_id"], user["id"])
        self.assertEqual(session["expires_at"], self.clock.now + 120)
        stored_values = [str(value) for value in tuple(session)]
        self.assertNotIn(token, stored_values)
        self.assertIn(hashlib.sha256(token.encode()).hexdigest(), stored_values)

    def test_each_login_issues_a_distinct_token(self) -> None:
        self.register("alice")
        self.assertNotEqual(self.login("alice"), self.login("alice"))

    def test_wrong_password_or_unknown_user_is_401(self) -> None:
        self.register("alice")
        for payload in [
            {"username": "alice", "password": "wrong-password"},
            {"username": "nobody", "password": PASSWORD},
        ]:
            with self.subTest(payload=payload):
                response = self.client.post("/auth/login", json=payload)
                self.assertEqual(response.status_code, 401)
                self.assertNotIn("access_token", response.json())
        self.assertEqual(self.query("SELECT * FROM sessions"), [])


class BearerAuthTests(ApiTestCase):
    session_ttl_seconds = 60

    def post_with(self, headers: dict[str, str]) -> int:
        response = self.client.post(
            "/posts", json={"title": "t", "content": "c"}, headers=headers
        )
        if response.status_code == 401:
            self.assertEqual(response.headers.get("www-authenticate"), "Bearer")
        return response.status_code

    def test_missing_malformed_or_forged_token_is_401_with_challenge(self) -> None:
        token = self.auth_header("alice")["Authorization"].removeprefix("Bearer ")
        for headers in [
            {},
            {"Authorization": token},
            {"Authorization": f"Basic {token}"},
            {"Authorization": "Bearer "},
            {"Authorization": "Bearer forged-token-value"},
            {"Authorization": f"Bearer {token}x"},
        ]:
            with self.subTest(headers=headers):
                self.assertEqual(self.post_with(headers), 401)
        self.assertEqual(self.query("SELECT * FROM posts"), [])

    def test_token_expires_after_ttl(self) -> None:
        headers = self.auth_header("alice")

        self.clock.now += 59
        self.assertEqual(self.post_with(headers), 201)
        self.clock.now += 1
        self.assertEqual(self.post_with(headers), 401)
        self.assertEqual(len(self.query("SELECT * FROM posts")), 1)


if __name__ == "__main__":
    unittest.main()
