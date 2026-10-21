"""`python -m uvicorn main:app`로 실제 서버를 띄워 환경 변수와 재시작 후 유지를 확인한다."""

import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class ServerProcess:
    def __init__(self, env: dict):
        self.port = free_port()
        self.base = f"http://127.0.0.1:{self.port}"
        self.proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "main:app", "--port", str(self.port)],
            cwd=ROOT,
            env={**os.environ, **env},
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

    def wait_ready(self):
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            if self.proc.poll() is not None:
                raise RuntimeError(self.proc.stdout.read().decode(errors="replace"))
            try:
                httpx.get(f"{self.base}/posts", timeout=1)
                return self
            except httpx.TransportError:
                time.sleep(0.2)
        raise TimeoutError("server did not start")

    def stop(self):
        if os.name == "nt":
            # Windows venv의 python.exe는 실제 인터프리터를 자식으로 띄우는 런처라서
            # 런처만 종료하면 서버가 잠시 남아 DB 파일을 잡고 있다. 트리 전체를 종료한다.
            subprocess.run(
                ["taskkill", "/T", "/F", "/PID", str(self.proc.pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        self.proc.terminate()
        self.proc.wait(timeout=10)
        self.proc.stdout.close()


class ServerRestartTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        # 서버 종료(addCleanup) 뒤에 임시 폴더를 지우도록 가장 먼저 등록한다.
        self.addCleanup(tmp.cleanup)
        self.db_path = Path(tmp.name) / "board.db"
        self.env = {"BOARD_DB_PATH": str(self.db_path), "SESSION_TTL_SECONDS": "90"}

    def start(self, env=None) -> ServerProcess:
        server = ServerProcess(env or self.env).wait_ready()
        self.addCleanup(lambda: server.proc.poll() is None and server.stop())
        return server

    def test_restart_keeps_users_posts_and_sessions(self):
        server = self.start()
        creds = {"username": "alice", "password": "password123"}
        self.assertEqual(httpx.post(f"{server.base}/auth/register", json=creds).status_code, 201)
        login = httpx.post(f"{server.base}/auth/login", json=creds).json()
        self.assertEqual(login["expires_in"], 90)
        headers = {"Authorization": f"Bearer {login['access_token']}"}
        post = httpx.post(f"{server.base}/posts", json={"title": "t", "content": "c"}, headers=headers).json()
        server.stop()
        self.assertTrue(self.db_path.exists())

        server = self.start()
        self.assertEqual(httpx.get(f"{server.base}/posts/{post['id']}").json(), post)
        res = httpx.put(f"{server.base}/posts/{post['id']}", json={"title": "t2", "content": "c2"}, headers=headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(httpx.post(f"{server.base}/auth/login", json=creds).status_code, 200)

    def test_invalid_ttl_fails_startup(self):
        proc = ServerProcess({**self.env, "SESSION_TTL_SECONDS": "0"}).proc
        try:
            output, _ = proc.communicate(timeout=20)
        finally:
            if proc.poll() is None:
                proc.kill()
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn(b"SESSION_TTL_SECONDS", output)


if __name__ == "__main__":
    unittest.main()
