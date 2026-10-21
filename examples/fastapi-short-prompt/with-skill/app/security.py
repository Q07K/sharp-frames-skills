import hashlib
import secrets

from pwdlib import PasswordHash

_password_hash = PasswordHash.recommended()

# Verified against when the username does not exist, so an unknown user costs
# the same Argon2 work as a wrong password and login timing does not reveal
# which usernames are registered.
_UNKNOWN_USER_HASH = _password_hash.hash(secrets.token_urlsafe(16))


def hash_password(password: str) -> str:
    return _password_hash.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    if password_hash is None:
        _password_hash.verify(password, _UNKNOWN_USER_HASH)
        return False
    return _password_hash.verify(password, password_hash)


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    """Only this digest is stored, so a leaked database does not yield live tokens.

    A fast hash is sufficient because tokens are 256-bit random values, not
    guessable passwords.
    """
    return hashlib.sha256(token.encode()).hexdigest()
