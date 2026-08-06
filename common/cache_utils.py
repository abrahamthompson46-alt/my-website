"""Cache backend helpers for health checks and diagnostics."""

from __future__ import annotations

from django.conf import settings


def get_cache_backend_label() -> str:
    backend = settings.CACHES["default"]["BACKEND"]
    lowered = backend.lower()
    if "redis" in lowered:
        return "redis"
    if "locmem" in lowered:
        return "locmem"
    if "dummy" in lowered:
        return "dummy"
    return backend.rsplit(".", 1)[-1]
