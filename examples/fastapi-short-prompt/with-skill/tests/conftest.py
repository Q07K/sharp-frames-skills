import sqlite3
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app

PASSWORD = "correct-horse-battery"


@pytest.fixture
def database_path(tmp_path: Path) -> str:
    return str(tmp_path / "test.db")


@pytest.fixture
def client(database_path: str) -> Iterator[TestClient]:
    with TestClient(create_app(database_path)) as test_client:
        yield test_client


@pytest.fixture
def db(database_path: str, client: TestClient) -> Iterator[sqlite3.Connection]:
    """Direct read access for asserting persisted state independently of the API."""
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()


AuthHeaders = dict[str, str]


@pytest.fixture
def signup_and_login(client: TestClient) -> Callable[[str], AuthHeaders]:
    def _signup_and_login(username: str) -> AuthHeaders:
        signup = client.post("/auth/signup", json={"username": username, "password": PASSWORD})
        assert signup.status_code == 201, signup.text
        login = client.post("/auth/login", json={"username": username, "password": PASSWORD})
        assert login.status_code == 200, login.text
        return {"Authorization": f"Bearer {login.json()['access_token']}"}

    return _signup_and_login
