"""Shared Redis cache and session configuration."""

from __future__ import annotations

from django.core.exceptions import ImproperlyConfigured


def apply_redis_settings(env, *, require: bool = False) -> dict | None:
    """
    When REDIS_URL is set, return Django settings overrides for Redis cache
    and cache-backed sessions. Raises if require=True and the URL is missing.
    """
    redis_url = env("REDIS_URL", default=None)
    if not redis_url:
        if require:
            raise ImproperlyConfigured(
                "Set REDIS_URL for cache, sessions, and rate limiting."
            )
        return None

    return {
        "CACHES": {
            "default": {
                "BACKEND": "django.core.cache.backends.redis.RedisCache",
                "LOCATION": redis_url,
            }
        },
        "SESSION_ENGINE": "django.contrib.sessions.backends.cache",
        "SESSION_CACHE_ALIAS": "default",
    }
