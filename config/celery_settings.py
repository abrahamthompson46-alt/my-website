"""Celery broker URL helpers."""

from __future__ import annotations

from urllib.parse import urlsplit, urlunsplit


def derive_celery_broker_url(redis_url: str | None, explicit: str | None = None) -> str:
    """
    Prefer CELERY_BROKER_URL; otherwise use Redis DB 1 derived from REDIS_URL.

    Falls back to an in-process memory broker for local/test without Redis.
    """
    if explicit:
        return explicit.strip()
    if not redis_url:
        return "memory://"

    parts = urlsplit(redis_url.strip())
    path = (parts.path or "").strip("/")
    if path.isdigit():
        # Prefer a separate Redis DB from Django cache/sessions (often /0).
        db = "1" if path == "0" else path
        new_path = f"/{db}"
    elif not path:
        new_path = "/1"
    else:
        new_path = parts.path or "/1"

    return urlunsplit((parts.scheme, parts.netloc, new_path, parts.query, parts.fragment))
