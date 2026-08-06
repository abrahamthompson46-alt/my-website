"""Production settings."""

from django.core.exceptions import ImproperlyConfigured

from config.settings.base import *  # noqa: F401, F403

DEBUG = False

_INSECURE_SECRET_KEYS = {
    "django-insecure-dev-only-change-before-production",
    "change-me-to-a-long-random-secret-key",
}
if SECRET_KEY in _INSECURE_SECRET_KEYS or len(SECRET_KEY) < 50:  # noqa: F405
    raise ImproperlyConfigured(
        "Set a strong DJANGO_SECRET_KEY (50+ characters) in production."
    )

# Required production host configuration
if not ALLOWED_HOSTS or set(ALLOWED_HOSTS) <= {"localhost", "127.0.0.1"}:  # noqa: F405
    raise ImproperlyConfigured(
        "Set DJANGO_ALLOWED_HOSTS to your production domain(s)."
    )

if not CSRF_TRUSTED_ORIGINS:  # noqa: F405
    raise ImproperlyConfigured(
        "Set CSRF_TRUSTED_ORIGINS to your HTTPS site origin(s), e.g. https://yourdomain.com"
    )

if DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3":  # noqa: F405
    raise ImproperlyConfigured("Use PostgreSQL in production — SQLite is not supported.")

if EMAIL_BACKEND == "django.core.mail.backends.console.EmailBackend":  # noqa: F405
    raise ImproperlyConfigured(
        "Configure SMTP email in production (EMAIL_BACKEND, EMAIL_HOST, etc.)."
    )

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)  # noqa: F405
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Redis — required in production for cache, sessions, and rate limits across workers
from config.redis_settings import apply_redis_settings  # noqa: E402

_redis_settings = apply_redis_settings(env, require=True)  # noqa: F405
CACHES = _redis_settings["CACHES"]  # noqa: F811
SESSION_ENGINE = _redis_settings["SESSION_ENGINE"]
SESSION_CACHE_ALIAS = _redis_settings["SESSION_CACHE_ALIAS"]

# Remove django-extensions from production if present
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != "django_extensions"]  # noqa: F405

WHITENOISE_MAX_AGE = 60 * 60 * 24 * 365
WHITENOISE_SKIP_COMPRESS_EXTENSIONS = ("jpg", "jpeg", "png", "gif", "webp", "svg", "ico", "woff", "woff2")

# Optional S3 media storage
_aws_bucket = env("AWS_STORAGE_BUCKET_NAME", default=None)  # noqa: F405
if _aws_bucket:
    AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID", default="")  # noqa: F405
    AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY", default="")  # noqa: F405
    AWS_STORAGE_BUCKET_NAME = _aws_bucket
    AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", default="us-east-1")  # noqa: F405
    AWS_S3_CUSTOM_DOMAIN = env("AWS_S3_CUSTOM_DOMAIN", default="")  # noqa: F405
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = False
    AWS_S3_FILE_OVERWRITE = False

    STORAGES["default"] = {  # noqa: F811
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "bucket_name": AWS_STORAGE_BUCKET_NAME,
            "region_name": AWS_S3_REGION_NAME,
            "custom_domain": AWS_S3_CUSTOM_DOMAIN or None,
        },
    }
    if AWS_S3_CUSTOM_DOMAIN:
        MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/"  # noqa: F811

# Optional error reporting
_sentry_dsn = env("SENTRY_DSN", default=None)  # noqa: F405
if _sentry_dsn:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=_sentry_dsn,
        integrations=[DjangoIntegration()],
        traces_sample_rate=env.float("SENTRY_TRACES_SAMPLE_RATE", default=0.1),  # noqa: F405
        send_default_pii=False,
    )
