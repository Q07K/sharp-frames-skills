"""Multi-request journeys, restart persistence, settings, and the real uvicorn entry point."""

import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

import httpx

from board.config import DEFAULT_DB_PATH, load_settings
from tests.support import PASSWORD, ApiTestCase

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TwoAuthorJourneyTests(ApiTestCase):
    session_ttl_seconds = 600

    def test_authors_visitor_and_restart(self) -> None:
        alice = self.register("alice")
        bob = self.register("bob")
        alice_headers = {"Authorization": f"Bearer {self.login('alice')}"}
        bob_headers = {"Authorization": f"Bearer {self.login('bob')}"}

        alice_post = self.create_post(alice_headers, "Alice", "by alice")
        bob_post = self.create_post(bob_headers, "Bob", "by bob")
        self.assertEqual(alice_post["author_id"], alice["id"])
        self.assertEqual(bob_post["author_id"], bob["id"])

        # Bob cannot touch Alice's post; Alice edits her own.
        self.assertEqual(
            self.client.delete(f"/posts/{alice_post['id']}", headers=bob_headers).status_code,
            403,
        )
        edited = self.client.put(
            f"/posts/{alice_post['id']}",
            json={"title": "Alice v2", "content": "edited"},
            headers=alice_headers,
        )
        self.assertEqual(edited.status_code, 200)

        self.restart()

        # Users, posts and unexpired sessions survive the restart.
        self.assertEqual(
            self.client.get("/posts").json(),
            [
                alice_post | {"title": "Alice v2", "content": "edited"},
                bob_post,
            ],
        )
        self.assertEqual(
            self.client.delete(f"/posts/{bob_post['id']}", headers=bob_headers).status_code,
            204,
        )
        self.login("alice")
        duplicate = self.client.post(
            "/auth/register", json={"username": "alice", "password": PASSWORD}
        )
        self.assertEqual(duplicate.status_code, 409)

        # A session that expired while the server was down stays rejected.
        self.clock.now += 600
        self.restart()
        expired = self.client.post(
            "/posts", json={"title": "late", "content": "late"}, headers=alice_headers
        )
        self.assertEqual(expired.status_code, 401)
        self.assertEqual(
            [post["id"] for post in self.client.get("/posts").json()], [alice_post["id"]]
        )


class SettingsTests(unittest.TestCase):
    def test_defaults(self) -> None:
        settings = load_settings({})
        self.assertEqual(settings.db_path, Path(DEFAULT_DB_PATH))
        self.assertEqual(settings.session_ttl_seconds, 3600)

    def test_reads_environment(self) -> None:
        settings = load_settings(
            {"BOARD_DB_PATH": "data/x.db", "SESSION_TTL_SECONDS": "15"}
        )
        self.assertEqual(settings.db_path, Path("data/x.db"))
        self.assertEqual(settings.session_ttl_seconds, 15)

    def test_rejects_non_positive_or_non_integer_ttl(self) -> None:
        for raw in ["0", "-5", "1.5", "abc", ""]:
            with self.subTest(raw=raw):
                with self.assertRaises(ValueError):
                    load_settings({"SESSION_TTL_SECONDS": raw})


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class UvicornEntryPointTests(unittest.TestCase):
    """Starts `python -m uvicorn main:app` exactly as documented, twice."""

    def start_server(self, db_path: Path, port: int) -> subprocess.Popen[bytes]:
        env = os.environ | {"BOARD_DB_PATH": str(db_path), "SESSION_TTL_SECONDS": "900"}
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "main:app", "--port", str(port)],
            cwd=PROJECT_ROOT,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise AssertionError(process.stderr.read().decode() if process.stderr else "exited")
            try:
                httpx.get(f"http://127.0.0.1:{port}/posts", timeout=1)
                return process
            except httpx.TransportError:
                time.sleep(0.2)
        process.kill()
        raise AssertionError("server did not start")

    def stop_server(self, process: subprocess.Popen[bytes]) -> None:
        process.terminate()
        process.wait(timeout=10)
        if process.stderr:
            process.stderr.close()

    def test_persists_across_process_restart(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "live.sqlite3"
            port = free_port()
            base = f"http://127.0.0.1:{port}"
            credentials = {"username": "alice", "password": PASSWORD}

            server = self.start_server(db_path, port)
            try:
                self.assertEqual(
                    httpx.post(f"{base}/auth/register", json=credentials).status_code, 201
                )
                login = httpx.post(f"{base}/auth/login", json=credentials).json()
                self.assertEqual(login["expires_in"], 900)
                headers = {"Authorization": f"Bearer {login['access_token']}"}
                created = httpx.post(
                    f"{base}/posts", json={"title": "t", "content": "c"}, headers=headers
                )
                self.assertEqual(created.status_code, 201)
            finally:
                self.stop_server(server)

            server = self.start_server(db_path, port)
            try:
                self.assertEqual(httpx.get(f"{base}/posts").json(), [created.json()])
                second = httpx.post(
                    f"{base}/posts", json={"title": "t2", "content": "c2"}, headers=headers
                )
                self.assertEqual(second.status_code, 201)
            finally:
                self.stop_server(server)


if __name__ == "__main__":
    unittest.main()
