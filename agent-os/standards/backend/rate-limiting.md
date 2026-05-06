# Rate Limiting & Caching Standards

Conventions for Redis-backed rate limiting (slowapi) and caching.

1. **Slowapi with Redis storage and moving-window.** Configure
   `Limiter(key_func=get_user_or_ip, storage_uri=settings.redis.url.get_secret_value(), strategy="moving-window")`.
   Moving-window (sliding log) is the most accurate strategy for an API where burst
   abuse matters.
2. **Composite key function.** Return `f"user:{user_id}"` when a valid JWT is present,
   fall back to `f"ip:{request.client.host}"` for anonymous traffic. Prevents shared-IP
   false positives behind NAT while still throttling unauthenticated abuse.
3. **Trust proxy headers carefully.** Only honor `X-Forwarded-For` when the request comes
   from a trusted proxy. Run uvicorn with
   `--proxy-headers --forwarded-allow-ips=<nginx-ip>` so `request.client.host` reflects
   the real client behind Nginx, not Nginx itself.
4. **Tier limits per endpoint.**
   - `@limiter.limit("5/minute")` on `/auth/login` and `/auth/refresh` — slow brute force.
   - `@limiter.limit("60/minute")` on checkout mutations.
   - Global `@limiter.limit("300/minute")` default applied as middleware.
5. **Separate Redis client for caching.** Use a dedicated `redis.asyncio.Redis` client
   (not the slowapi-managed one) for application caching. Always set explicit TTLs on
   `set`. Use a `cache:` key namespace prefix. Share the same Redis instance, separate
   logical key namespaces. Dispose connections in lifespan shutdown.
