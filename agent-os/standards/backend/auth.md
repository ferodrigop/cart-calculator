# Authentication Standards

Conventions for the OAuth2 password flow with JWTs (Authlib).

1. **Hash with Argon2.** Use `argon2-cffi` (via `passlib[argon2]` or directly through
   `argon2.PasswordHasher`). Never use bcrypt for new code, never store plaintext, never
   roll your own hashing.
2. **Encode JWTs with Authlib.** Use `authlib.jose.jwt` with `HS256` (or `RS256` if you
   have key management). Set `sub` to an immutable user UUID — never username or email.
   Always include `exp`, `iat`, `jti`, and a `type` claim of `"access"` or `"refresh"`.
3. **Short access, longer refresh, with rotation.** Access tokens expire in 15 minutes,
   refresh tokens in 7-14 days. Implement refresh-token rotation backed by a Redis
   denylist keyed by `jti`. On refresh, atomically `SET NX` the old `jti` as "used" so
   two concurrent refreshes can't both succeed.
4. **Secrets via `pydantic-settings` `SecretStr`.** Never hardcode the JWT secret. Require
   it in production via a validator (min length, no default). Support an old-and-new
   secret pair during rotation windows.
5. **OAuth2 password flow.** `OAuth2PasswordBearer(tokenUrl="auth/login")` is the security
   scheme for OpenAPI docs only. The login endpoint accepts `OAuth2PasswordRequestForm`
   and returns `{"access_token", "refresh_token", "token_type": "bearer"}`. Protect
   routes with `CurrentUser = Annotated[User, Depends(get_current_user)]`.
