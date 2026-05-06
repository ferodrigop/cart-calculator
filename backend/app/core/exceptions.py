from __future__ import annotations


class AuthError(Exception):
    """Base for authentication-domain errors. Translated to HTTP at the boundary."""

    status_code: int = 400
    detail: str = "authentication error"

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(detail or self.detail)
        if detail is not None:
            self.detail = detail


class EmailAlreadyExistsError(AuthError):
    status_code = 409
    detail = "email already registered"


class InvalidCredentialsError(AuthError):
    status_code = 401
    detail = "invalid credentials"


class InvalidTokenError(AuthError):
    status_code = 401
    detail = "invalid token"


class TokenExpiredError(AuthError):
    status_code = 401
    detail = "token expired"


class RefreshTokenReusedError(AuthError):
    status_code = 401
    detail = "refresh token already used"


class UserNotFoundError(AuthError):
    status_code = 404
    detail = "user not found"
