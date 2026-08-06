"""Development settings."""

from config.settings.base import *  # noqa: F401, F403

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

# Use SQLite locally unless PostgreSQL is explicitly configured.
if env("DB_ENGINE", default="django.db.backends.sqlite3") == "django.db.backends.sqlite3":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / env("DB_NAME", default="db.sqlite3"),
        }
    }

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

INSTALLED_APPS += [  # noqa: F405
    "debug_toolbar",
]

MIDDLEWARE += [  # noqa: F405
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

INTERNAL_IPS = ["127.0.0.1"]

DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda request: DEBUG,
}

# Use simpler static storage in development
STORAGES["staticfiles"]["BACKEND"] = (  # noqa: F405
    "django.contrib.staticfiles.storage.StaticFilesStorage"
)

# When REDIS_URL is set (e.g. docker compose), base.py enables Redis cache and sessions.
# Start Redis locally: docker compose up redis -d

# Log SQL queries at DEBUG level when needed
# LOGGING["loggers"]["django.db.backends"]["level"] = "DEBUG"
