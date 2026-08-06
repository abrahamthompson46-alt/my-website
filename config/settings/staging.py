"""Staging settings — production-like with debug tooling disabled."""

from config.redis_settings import apply_redis_settings
from config.settings.base import *  # noqa: F401, F403

DEBUG = False

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Require Redis in staging (same as production)
_redis_settings = apply_redis_settings(env, require=True)  # noqa: F405
CACHES = _redis_settings["CACHES"]  # noqa: F811
SESSION_ENGINE = _redis_settings["SESSION_ENGINE"]
SESSION_CACHE_ALIAS = _redis_settings["SESSION_CACHE_ALIAS"]
