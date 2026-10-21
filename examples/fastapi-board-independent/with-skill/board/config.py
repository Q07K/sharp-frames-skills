import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

DEFAULT_DB_PATH = "board.sqlite3"
DEFAULT_SESSION_TTL_SECONDS = 3600


@dataclass(frozen=True)
class Settings:
    db_path: Path
    session_ttl_seconds: int


def load_settings(environ: Mapping[str, str] = os.environ) -> Settings:
    """Read settings from environment variables.

    Raises ValueError when SESSION_TTL_SECONDS is not a positive integer, so a
    misconfigured server fails at startup instead of issuing unusable sessions.
    """
    db_path = environ.get("BOARD_DB_PATH") or DEFAULT_DB_PATH
    raw_ttl = environ.get("SESSION_TTL_SECONDS", str(DEFAULT_SESSION_TTL_SECONDS))
    try:
        ttl_seconds = int(raw_ttl.strip())
    except ValueError:
        raise ValueError(
            f"SESSION_TTL_SECONDS must be a positive integer, got {raw_ttl!r}"
        ) from None
    if ttl_seconds <= 0:
        raise ValueError(
            f"SESSION_TTL_SECONDS must be a positive integer, got {raw_ttl!r}"
        )
    return Settings(db_path=Path(db_path), session_ttl_seconds=ttl_seconds)
