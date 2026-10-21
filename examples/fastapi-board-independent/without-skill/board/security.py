"""비밀번호 해시와 세션 토큰."""

import hashlib
import secrets

from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

_password_hash = PasswordHash((Argon2Hasher(),))

# 존재하지 않는 사용자로 로그인할 때도 같은 비용의 검증을 수행해
# 응답 시간으로 사용자 존재 여부가 드러나지 않게 한다.
_DUMMY_HASH = _password_hash.hash(secrets.token_urlsafe(16))


def hash_password(password: str) -> str:
    return _password_hash.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    if password_hash is None:
        _password_hash.verify(password, _DUMMY_HASH)
        return False
    return _password_hash.verify(password, password_hash)


def new_token() -> str:
    return secrets.token_urlsafe(32)


def token_fingerprint(token: str) -> str:
    # 토큰은 충분한 엔트로피를 가진 난수이므로 솔트 없는 SHA-256으로 충분하다.
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
