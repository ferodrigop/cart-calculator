from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID, uuid4

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from authlib.jose import JoseError, jwt

from app.core.config import Settings
from app.core.exceptions import InvalidTokenError

TokenType = Literal["access", "refresh"]

_hasher = PasswordHasher()


def hash_password(plain: str) -> str:
    return _hasher.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _hasher.verify(hashed, plain)
    except VerifyMismatchError:
        return False
    except Exception:  # malformed hash, etc.
        return False


def _now() -> int:
    return int(datetime.now(UTC).timestamp())


def _encode(secret: str, claims: dict[str, Any], algorithm: str) -> str:
    token = jwt.encode({"alg": algorithm}, claims, secret)
    if isinstance(token, bytes):
        return token.decode("ascii")
    return str(token)


def mint_access(user_id: UUID, settings: Settings) -> str:
    iat = _now()
    claims = {
        "sub": str(user_id),
        "type": "access",
        "iat": iat,
        "exp": iat + settings.jwt.access_ttl_seconds,
        "jti": uuid4().hex,
    }
    return _encode(
        settings.jwt.access_secret.get_secret_value(),
        claims,
        settings.jwt.algorithm,
    )


def mint_refresh(user_id: UUID, settings: Settings) -> str:
    iat = _now()
    claims = {
        "sub": str(user_id),
        "type": "refresh",
        "iat": iat,
        "exp": iat + settings.jwt.refresh_ttl_seconds,
        "jti": uuid4().hex,
    }
    return _encode(
        settings.jwt.refresh_secret.get_secret_value(),
        claims,
        settings.jwt.algorithm,
    )


def decode_token(
    token: str,
    secret: str,
    expected_type: TokenType,
) -> dict[str, Any]:
    try:
        claims = jwt.decode(token, secret)
        claims.validate(now=_now(), leeway=0)
    except JoseError as exc:
        raise InvalidTokenError("invalid token") from exc
    except Exception as exc:  # malformed token, etc.
        raise InvalidTokenError("invalid token") from exc

    if claims.get("type") != expected_type:
        raise InvalidTokenError("token type mismatch")
    sub = claims.get("sub")
    if not isinstance(sub, str):
        raise InvalidTokenError("missing subject")
    jti = claims.get("jti")
    if not isinstance(jti, str):
        raise InvalidTokenError("missing jti")
    exp = claims.get("exp")
    if not isinstance(exp, int):
        raise InvalidTokenError("missing exp")
    return dict(claims)
