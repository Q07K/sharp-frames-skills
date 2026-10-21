"""환경 변수에서 실행 설정을 읽는다."""

import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = PROJECT_ROOT / "board.db"
DEFAULT_SESSION_TTL_SECONDS = 3600


@dataclass(frozen=True)
class Settings:
    db_path: Path
    session_ttl_seconds: int


def parse_ttl(raw: str) -> int:
    text = raw.strip()
    # int()는 "+5", "1_000" 같은 표기도 받아들이므로 숫자만 허용한다.
    if not text.isascii() or not text.isdigit():
        raise ValueError(f"SESSION_TTL_SECONDS must be a positive integer, got {raw!r}")
    value = int(text)
    if value <= 0:
        raise ValueError(f"SESSION_TTL_SECONDS must be a positive integer, got {raw!r}")
    return value


def load_settings() -> Settings:
    db_path = os.environ.get("BOARD_DB_PATH", "").strip()
    raw_ttl = os.environ.get("SESSION_TTL_SECONDS")
    return Settings(
        db_path=Path(db_path) if db_path else DEFAULT_DB_PATH,
        session_ttl_seconds=(
            DEFAULT_SESSION_TTL_SECONDS if raw_ttl is None else parse_ttl(raw_ttl)
        ),
    )
