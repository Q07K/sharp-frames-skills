import sqlite3
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from board.app import create_app
from board.config import Settings

PASSWORD = "correct-horse"


class FakeClock:
    def __init__(self, now: float = 1_000_000.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now


class ApiTestCase(unittest.TestCase):
    """Runs requests through the real app and a disposable SQLite file."""

    session_ttl_seconds = 3600

    def setUp(self) -> None:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.db_path = Path(temp_dir.name) / "board.sqlite3"
        self.clock = FakeClock()
        self.client = self.start_client()

    def start_client(self) -> TestClient:
        settings = Settings(
            db_path=self.db_path, session_ttl_seconds=self.session_ttl_seconds
        )
        client = TestClient(create_app(settings, clock=self.clock))
        client.__enter__()
        self.addCleanup(client.__exit__, None, None, None)
        return client

    def restart(self) -> None:
        self.client.__exit__(None, None, None)
        self.client = self.start_client()

    def query(self, sql: str, params: tuple[object, ...] = ()) -> list[sqlite3.Row]:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        try:
            return connection.execute(sql, params).fetchall()
        finally:
            connection.close()

    def register(self, username: str, password: str = PASSWORD) -> dict[str, object]:
        response = self.client.post(
            "/auth/register", json={"username": username, "password": password}
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def login(self, username: str, password: str = PASSWORD) -> str:
        response = self.client.post(
            "/auth/login", json={"username": username, "password": password}
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()["access_token"]

    def auth_header(self, username: str) -> dict[str, str]:
        self.register(username)
        return {"Authorization": f"Bearer {self.login(username)}"}

    def create_post(
        self, headers: dict[str, str], title: str = "Title", content: str = "Body"
    ) -> dict[str, object]:
        response = self.client.post(
            "/posts", json={"title": title, "content": content}, headers=headers
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()
