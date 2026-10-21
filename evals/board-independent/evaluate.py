"""Black-box HTTP contracts; no candidate module names or DB schema assumptions."""

import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest

import httpx


class Contracts(unittest.TestCase):
    candidate: Path
    interpreter: str

    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory()
        self.addCleanup(self.workspace.cleanup)
        self.db_path = Path(self.workspace.name) / "board.sqlite3"
        self.ttl = 2 if self._testMethodName == "test_expired_session" else 3600
        self.process = None
        self.client = None
        self.addCleanup(self.stop)
        self.start()

    def start(self):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        env = dict(os.environ, BOARD_DB_PATH=str(self.db_path), SESSION_TTL_SECONDS=str(self.ttl), PYTHONUTF8="1")
        self.process = subprocess.Popen(
            [self.interpreter, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", str(port)],
            cwd=self.candidate, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", errors="replace",
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        self.client = httpx.Client(base_url=f"http://127.0.0.1:{port}", timeout=10)
        for _ in range(150):
            if self.process.poll() is not None:
                _, diagnostics = self.process.communicate(timeout=10)
                self.fail("Startup failed: " + diagnostics)
            try:
                if self.client.get("/openapi.json").status_code == 200:
                    return
            except httpx.TransportError:
                pass
            time.sleep(0.1)
        self.fail("Startup timed out")

    def stop(self):
        if self.client is not None:
            self.client.close()
            self.client = None
        if self.process is not None:
            if self.process.poll() is None:
                self.process.terminate()
            self.process.communicate(timeout=10)
            self.process = None

    def account(self, name="alice"):
        credentials = {"username": name, "password": "test-password-123"}
        registered = self.client.post("/auth/register", json=credentials)
        self.assertEqual(registered.status_code, 201, registered.text)
        self.assertEqual(set(registered.json()), {"id", "username"})
        logged_in = self.client.post("/auth/login", json=credentials)
        self.assertEqual(logged_in.status_code, 200, logged_in.text)
        self.assertEqual(set(logged_in.json()), {"access_token", "token_type", "expires_in"})
        self.assertEqual(logged_in.json()["token_type"], "bearer")
        self.assertEqual(logged_in.json()["expires_in"], self.ttl)
        return registered.json(), {"Authorization": "Bearer " + logged_in.json()["access_token"]}

    def post(self, headers, title="First post", content="Hello"):
        response = self.client.post("/posts", headers=headers, json={"title": title, "content": content})
        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(set(response.json()), {"id", "title", "content", "author_id"})
        self.assertIsInstance(response.json()["id"], int)
        return response.json()

    def test_registration_and_login(self):
        user, headers = self.account()
        self.assertEqual(user["username"], "alice")
        duplicate = self.client.post("/auth/register", json={"username": "alice", "password": "other-password"})
        self.assertEqual(duplicate.status_code, 409, duplicate.text)
        for name in ("alice", "missing"):
            bad = self.client.post("/auth/login", json={"username": name, "password": "wrong-password"})
            self.assertEqual(bad.status_code, 401, bad.text)
        self.assertEqual(self.post(headers)["author_id"], user["id"])

    def test_author_crud(self):
        user, headers = self.account()
        post = self.post(headers)
        self.assertEqual(post["author_id"], user["id"])
        url = f"/posts/{post['id']}"
        self.assertEqual(self.client.get(url).json(), post)
        self.assertEqual(self.client.get("/posts").json(), [post])
        changed = self.client.put(url, headers=headers, json={"title": " Updated ", "content": " Changed "})
        self.assertEqual(changed.status_code, 200, changed.text)
        self.assertEqual(changed.json(), dict(post, title="Updated", content="Changed"))
        self.assertEqual(self.client.get(url).json(), changed.json())
        deleted = self.client.delete(url, headers=headers)
        self.assertEqual(deleted.status_code, 204, deleted.text)
        self.assertEqual(deleted.content, b"")
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.get("/posts").json(), [])

    def test_anonymous_cannot_write(self):
        _, headers = self.account()
        post = self.post(headers)
        url = f"/posts/{post['id']}"
        responses = [self.client.post("/posts", json={"title": "x", "content": "y"}),
                     self.client.put(url, json={"title": "x", "content": "y"}), self.client.delete(url)]
        for response in responses:
            self.assertEqual(response.status_code, 401, response.text)
            self.assertEqual(response.headers.get("www-authenticate", "").lower(), "bearer")
        self.assertEqual(self.client.get(url).json(), post)

    def test_other_author_is_denied(self):
        _, alice = self.account()
        post = self.post(alice)
        _, bob = self.account("bob")
        url = f"/posts/{post['id']}"
        denied = self.client.put(url, headers=bob, json={"title": "stolen", "content": "changed"})
        self.assertEqual(denied.status_code, 403, denied.text)
        self.assertEqual(self.client.delete(url, headers=bob).status_code, 403)
        self.assertEqual(self.client.get(url).json(), post)
        self.assertEqual(self.client.delete(url, headers=alice).status_code, 204)

    def test_forged_token_is_denied(self):
        _, headers = self.account()
        post = self.post(headers)
        fake = {"Authorization": "Bearer not-a-real-token"}
        response = self.client.delete(f"/posts/{post['id']}", headers=fake)
        self.assertEqual(response.status_code, 401, response.text)
        self.assertEqual(response.headers.get("www-authenticate", "").lower(), "bearer")
        self.assertEqual(self.client.get(f"/posts/{post['id']}").json(), post)

    def test_validation_and_pagination(self):
        _, headers = self.account()
        for data in ({"title": " ", "content": "x"}, {"title": "x" * 121, "content": "x"},
                     {"title": "x", "content": " "}, {"title": "x", "content": "y", "author_id": 999}):
            response = self.client.post("/posts", headers=headers, json=data)
            self.assertEqual(response.status_code, 422, response.text)
        self.assertEqual(self.client.get("/posts").json(), [])
        first = self.post(headers)
        second = self.post(headers)
        self.assertLess(first["id"], second["id"])
        self.assertEqual(self.client.get("/posts?limit=1&offset=1").json(), [second])
        for query in ("limit=0", "limit=101", "offset=-1"):
            self.assertEqual(self.client.get("/posts?" + query).status_code, 422)
        for credentials in ({"username": "ab", "password": "long-password"},
                            {"username": "new_user", "password": "short"}):
            self.assertEqual(self.client.post("/auth/register", json=credentials).status_code, 422)

    def test_missing_post(self):
        _, headers = self.account()
        self.assertEqual(self.client.get("/posts/999").status_code, 404)
        self.assertEqual(self.client.put("/posts/999", headers=headers, json={"title": "x", "content": "y"}).status_code, 404)
        self.assertEqual(self.client.delete("/posts/999", headers=headers).status_code, 404)

    def test_restart_preserves_data_and_session(self):
        _, headers = self.account()
        post = self.post(headers)
        self.stop()
        self.start()
        self.assertEqual(self.client.get(f"/posts/{post['id']}").json(), post)
        self.assertEqual(self.client.delete(f"/posts/{post['id']}", headers=headers).status_code, 204)

    def test_expired_session(self):
        _, headers = self.account()
        post = self.post(headers)
        time.sleep(2.2)
        response = self.client.delete(f"/posts/{post['id']}", headers=headers)
        self.assertEqual(response.status_code, 401, response.text)
        self.assertEqual(response.headers.get("www-authenticate", "").lower(), "bearer")
        self.assertEqual(self.client.get(f"/posts/{post['id']}").json(), post)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--python", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    Contracts.candidate = args.candidate.resolve()
    Contracts.interpreter = args.python
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Contracts)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    failures = {test._testMethodName: detail for test, detail in result.failures + result.errors}
    records = {name: {"passed": name not in failures, "detail": failures.get(name)}
               for name in unittest.defaultTestLoader.getTestCaseNames(Contracts)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"tests_run": result.testsRun, "cases": records}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
