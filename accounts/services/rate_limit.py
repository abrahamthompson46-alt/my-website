import hashlib
import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger("security")


def _client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _client_user_agent(request):
    return request.META.get("HTTP_USER_AGENT", "")[:500]


def is_rate_limited(key, limit, window_seconds):
    cache_key = f"ratelimit:{key}"
    count = cache.get(cache_key, 0)
    if count >= limit:
        return True
    if count == 0:
        cache.set(cache_key, 1, window_seconds)
    else:
        cache.incr(cache_key)
    return False


def check_auth_rate_limit(request, scope, identifier="", limit=5, window_seconds=900):
    ip = _client_ip(request) or "unknown"
    key = f"{scope}:{ip}:{identifier}".lower()
    return is_rate_limited(key, limit, window_seconds)


def reset_auth_rate_limit(request, scope, identifier=""):
    ip = _client_ip(request) or "unknown"
    cache.delete(f"ratelimit:{scope}:{ip}:{identifier}".lower())


def log_rate_limit_exceeded(request, scope):
    logger.warning(
        "Rate limit exceeded",
        extra={
            "scope": scope,
            "ip": _client_ip(request),
            "path": request.path,
        },
    )
