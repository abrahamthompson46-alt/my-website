"""Cache and Redis diagnostics for the control room."""

from __future__ import annotations

import time
from urllib.parse import urlparse

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from common.cache_utils import get_cache_backend_label
from control_room.services import CACHE_TTL, NAV_CACHE_PREFIX, SETTINGS_CACHE_KEY

PROBE_LOG_KEY = "control_room:cache_probe_log"
PROBE_LOG_MAX = 8
PROBE_KEY = "control_room:cache_probe"

NAV_MENU_CODES = (
    "public_header",
    "public_footer",
    "customer_portal",
    "operations",
    "partner_portal",
    "control_room",
)


def mask_redis_url(url: str) -> str:
    if not url:
        return "Not configured"
    parsed = urlparse(url)
    host = parsed.hostname or "unknown"
    port = parsed.port or 6379
    db = parsed.path.lstrip("/") or "0"
    return f"redis://{host}:{port}/{db}"


def probe_cache() -> dict:
    token = f"probe-{time.time()}"
    start = time.perf_counter()
    try:
        cache.set(PROBE_KEY, token, 30)
        ok = cache.get(PROBE_KEY) == token
        cache.delete(PROBE_KEY)
        latency_ms = round((time.perf_counter() - start) * 1000, 1)
        return {"ok": ok, "latency_ms": latency_ms, "error": ""}
    except Exception as exc:
        return {"ok": False, "latency_ms": None, "error": str(exc)}


def get_redis_server_info() -> dict | None:
    if get_cache_backend_label() != "redis":
        return None
    try:
        client = cache.client.get_client()
        info = client.info()
        return {
            "version": info.get("redis_version", "—"),
            "used_memory_human": info.get("used_memory_human", "—"),
            "connected_clients": info.get("connected_clients", 0),
            "uptime_days": info.get("uptime_in_days", 0),
        }
    except Exception as exc:
        return {"error": str(exc)}


def _record_probe(probe: dict) -> None:
    if not probe.get("ok"):
        status = "error"
    else:
        status = "healthy"

    entry = {
        "at": timezone.now(),
        "status": status,
        "latency_ms": probe.get("latency_ms"),
        "error": probe.get("error", ""),
    }

    log = cache.get(PROBE_LOG_KEY) or []
    if log and log[-1].get("status") == entry["status"] and log[-1].get("latency_ms") == entry["latency_ms"]:
        return
    log.append(entry)
    cache.set(PROBE_LOG_KEY, log[-PROBE_LOG_MAX:], 60 * 60 * 24)


def get_recent_probes() -> list[dict]:
    return list(reversed(cache.get(PROBE_LOG_KEY) or []))


def get_cache_diagnostics() -> dict:
    backend = get_cache_backend_label()
    location = settings.CACHES["default"].get("LOCATION", "")
    session_engine = settings.SESSION_ENGINE
    sessions_use_cache = "cache" in session_engine

    platform_cached = cache.get(SETTINGS_CACHE_KEY) is not None
    nav_cached = sum(1 for code in NAV_MENU_CODES if cache.get(f"{NAV_CACHE_PREFIX}{code}") is not None)

    probe = probe_cache()
    _record_probe(probe)

    redis_info = get_redis_server_info() if backend == "redis" else None
    redis_active = backend == "redis" and probe["ok"] and redis_info is not None and "error" not in redis_info

    uses = [
        {
            "name": "Platform settings",
            "detail": SETTINGS_CACHE_KEY,
            "active": platform_cached,
            "ttl": f"{CACHE_TTL}s",
        },
        {
            "name": "Navigation menus",
            "detail": f"{nav_cached}/{len(NAV_MENU_CODES)} menus cached",
            "active": nav_cached > 0,
            "ttl": f"{CACHE_TTL}s",
        },
        {
            "name": "User sessions",
            "detail": "Shared across workers" if sessions_use_cache else "Database sessions",
            "active": sessions_use_cache,
            "ttl": f"{settings.SESSION_COOKIE_AGE // 86400}d",
        },
        {
            "name": "Auth rate limits",
            "detail": "ratelimit:* keys",
            "active": backend == "redis",
            "ttl": f"{getattr(settings, 'AUTH_LOGIN_RATE_WINDOW', 900)}s window",
        },
    ]

    if backend == "redis" and not probe["ok"]:
        recommendation = "Redis is configured but the cache probe failed. Check that Redis is running and REDIS_URL is correct."
    elif backend == "locmem":
        recommendation = "Using in-memory cache. Set REDIS_URL in .env and start Redis for shared sessions and rate limits across workers."
    else:
        recommendation = ""

    return {
        "backend": backend,
        "backend_label": backend.upper(),
        "redis_active": redis_active,
        "redis_url": mask_redis_url(location) if backend == "redis" else "In-memory (not shared)",
        "session_engine": session_engine.rsplit(".", 1)[-1],
        "sessions_use_cache": sessions_use_cache,
        "probe": probe,
        "redis_info": redis_info,
        "uses": uses,
        "recent_probes": get_recent_probes(),
        "recommendation": recommendation,
        "checked_at": timezone.now(),
    }
