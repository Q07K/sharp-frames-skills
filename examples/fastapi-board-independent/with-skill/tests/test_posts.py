import unittest

from tests.support import ApiTestCase


def post_rows(test: ApiTestCase) -> list[tuple[object, ...]]:
    return [tuple(row) for row in test.query("SELECT * FROM posts ORDER BY id")]


class CreatePostTests(ApiTestCase):
    def test_create_sets_author_from_token_and_trims_text(self) -> None:
        alice = self.register("alice")
        headers = {"Authorization": f"Bearer {self.login('alice')}"}

        response = self.client.post(
            "/posts", json={"title": "  Hello  ", "content": "\n Body \t"}, headers=headers
        )

        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(set(body), {"id", "title", "content", "author_id"})
        self.assertIsInstance(body["id"], int)
        self.assertEqual(body["title"], "Hello")
        self.assertEqual(body["content"], "Body")
        self.assertEqual(body["author_id"], alice["id"])
        self.assertEqual(
            post_rows(self), [(body["id"], "Hello", "Body", alice["id"])]
        )

    def test_client_supplied_author_id_or_extra_field_is_422(self) -> None:
        headers = self.auth_header("alice")
        for payload in [
            {"title": "t", "content": "c", "author_id": 999},
            {"title": "t", "content": "c", "id": 5},
        ]:
            with self.subTest(payload=payload):
                response = self.client.post("/posts", json=payload, headers=headers)
                self.assertEqual(response.status_code, 422)
        self.assertEqual(post_rows(self), [])

    def test_title_and_content_length_boundaries_after_trimming(self) -> None:
        headers = self.auth_header("alice")
        valid = [
            {"title": "a", "content": "b"},
            {"title": " " + "a" * 120 + " ", "content": " " + "b" * 5000 + " "},
        ]
        for payload in valid:
            with self.subTest(payload_lengths=(len(payload["title"]), len(payload["content"]))):
                response = self.client.post("/posts", json=payload, headers=headers)
                self.assertEqual(response.status_code, 201, response.text)

        invalid = [
            {"title": "", "content": "c"},
            {"title": "   ", "content": "c"},
            {"title": "a" * 121, "content": "c"},
            {"title": "t", "content": ""},
            {"title": "t", "content": " \n\t "},
            {"title": "t", "content": "b" * 5001},
            {"title": None, "content": "c"},
            {"title": 123, "content": "c"},
            {"content": "c"},
            {"title": "t"},
        ]
        for payload in invalid:
            with self.subTest(payload=payload):
                response = self.client.post("/posts", json=payload, headers=headers)
                self.assertEqual(response.status_code, 422, response.text)
        self.assertEqual(len(post_rows(self)), len(valid))

    def test_malformed_json_body_is_422(self) -> None:
        headers = self.auth_header("alice") | {"Content-Type": "application/json"}
        response = self.client.post("/posts", content=b"{not json", headers=headers)
        self.assertEqual(response.status_code, 422)
        self.assertEqual(post_rows(self), [])


class ReadPostTests(ApiTestCase):
    def test_list_and_detail_are_public(self) -> None:
        created = self.create_post(self.auth_header("alice"), "First", "One")

        listed = self.client.get("/posts")
        detail = self.client.get(f"/posts/{created['id']}")

        self.assertEqual(listed.status_code, 200)
        self.assertEqual(listed.json(), [created])
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json(), created)

    def test_missing_post_is_404(self) -> None:
        for post_id in ["1", "0", "-1", str(2**70)]:
            with self.subTest(post_id=post_id):
                self.assertEqual(self.client.get(f"/posts/{post_id}").status_code, 404)

    def test_non_integer_post_id_is_422(self) -> None:
        self.assertEqual(self.client.get("/posts/abc").status_code, 422)

    def test_list_orders_by_id_and_paginates(self) -> None:
        alice = self.auth_header("alice")
        bob = self.auth_header("bob")
        ids = [
            self.create_post(alice if n % 2 else bob, f"Post {n}", "c")["id"]
            for n in range(25)
        ]

        def listed_ids(params: dict[str, object]) -> list[int]:
            response = self.client.get("/posts", params=params)
            self.assertEqual(response.status_code, 200, response.text)
            return [post["id"] for post in response.json()]

        self.assertEqual(listed_ids({}), ids[:20])
        self.assertEqual(listed_ids({"limit": 1}), ids[:1])
        self.assertEqual(listed_ids({"limit": 100}), ids)
        self.assertEqual(listed_ids({"limit": 5, "offset": 10}), ids[10:15])
        self.assertEqual(listed_ids({"offset": 24}), ids[24:])
        self.assertEqual(listed_ids({"offset": 25}), [])

    def test_invalid_page_range_is_422(self) -> None:
        for params in [
            {"limit": 0},
            {"limit": 101},
            {"limit": -1},
            {"offset": -1},
            {"limit": "many"},
            {"offset": 2**70},
        ]:
            with self.subTest(params=params):
                self.assertEqual(self.client.get("/posts", params=params).status_code, 422)


class UpdateDeletePostTests(ApiTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.alice = self.auth_header("alice")
        self.bob = self.auth_header("bob")
        self.post = self.create_post(self.alice, "Original", "Original body")

    def test_author_replaces_title_and_content(self) -> None:
        response = self.client.put(
            f"/posts/{self.post['id']}",
            json={"title": " New ", "content": " New body "},
            headers=self.alice,
        )

        self.assertEqual(response.status_code, 200)
        expected = self.post | {"title": "New", "content": "New body"}
        self.assertEqual(response.json(), expected)
        self.assertEqual(self.client.get(f"/posts/{self.post['id']}").json(), expected)

    def test_update_requires_full_body_and_rejects_extra_fields(self) -> None:
        before = post_rows(self)
        for payload in [
            {"title": "Only title"},
            {"content": "Only content"},
            {"title": "t", "content": "c", "author_id": 2},
            {"title": "", "content": "c"},
        ]:
            with self.subTest(payload=payload):
                response = self.client.put(
                    f"/posts/{self.post['id']}", json=payload, headers=self.alice
                )
                self.assertEqual(response.status_code, 422)
        self.assertEqual(post_rows(self), before)

    def test_author_deletes_post(self) -> None:
        response = self.client.delete(f"/posts/{self.post['id']}", headers=self.alice)

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")
        self.assertEqual(self.client.get(f"/posts/{self.post['id']}").status_code, 404)
        self.assertEqual(post_rows(self), [])
        self.assertEqual(
            self.client.delete(f"/posts/{self.post['id']}", headers=self.alice).status_code,
            404,
        )

    def test_other_user_gets_403_and_post_is_unchanged(self) -> None:
        before = post_rows(self)

        update = self.client.put(
            f"/posts/{self.post['id']}",
            json={"title": "Hijack", "content": "Hijack"},
            headers=self.bob,
        )
        delete = self.client.delete(f"/posts/{self.post['id']}", headers=self.bob)

        self.assertEqual(update.status_code, 403)
        self.assertEqual(delete.status_code, 403)
        self.assertEqual(post_rows(self), before)

    def test_missing_post_update_or_delete_is_404_for_logged_in_user(self) -> None:
        for post_id in [self.post["id"] + 100, 2**70]:
            with self.subTest(post_id=post_id):
                update = self.client.put(
                    f"/posts/{post_id}", json={"title": "t", "content": "c"}, headers=self.bob
                )
                delete = self.client.delete(f"/posts/{post_id}", headers=self.bob)
                self.assertEqual(update.status_code, 404)
                self.assertEqual(delete.status_code, 404)

    def test_write_endpoints_require_authentication(self) -> None:
        before = post_rows(self)
        path = f"/posts/{self.post['id']}"
        for response in [
            self.client.put(path, json={"title": "t", "content": "c"}),
            self.client.delete(path),
            self.client.put(
                path,
                json={"title": "t", "content": "c"},
                headers={"Authorization": "Bearer forged"},
            ),
        ]:
            with self.subTest(method=response.request.method):
                self.assertEqual(response.status_code, 401)
                self.assertEqual(response.headers.get("www-authenticate"), "Bearer")
        self.assertEqual(post_rows(self), before)


if __name__ == "__main__":
    unittest.main()
