"""Base settings shared across all environments."""

from pathlib import Path

from config.env import BASE_DIR, env

# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------

SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="django-insecure-dev-only-change-before-production",
)

DEBUG = env.bool("DJANGO_DEBUG", default=False)

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

SITE_URL = env("SITE_URL", default="http://localhost:8000")
SITE_NAME = env("SITE_NAME", default="Enterprise Platform")

ROOT_URLCONF = "config.urls"

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django.contrib.sitemaps",
]

THIRD_PARTY_APPS = [
    "django_extensions",
]

LOCAL_APPS = [
    "core",
    "common.apps.CommonConfig",
    "accounts.apps.AccountsConfig",
    "cms",
    "marketing",
    "website",
    "products",
    "pages",
    "blog",
    "documentation",
    "careers",
    "contact",
    "support",
    "customer_portal",
    "payments.apps.PaymentsConfig",
    "operations.apps.OperationsConfig",
    "control_room.apps.ControlRoomConfig",
    "partners",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.gzip.GZipMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.http.ConditionalGetMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "accounts.middleware.SecurityHeadersMiddleware",
    "accounts.middleware.SessionActivityMiddleware",
    "accounts.middleware.StaffMFARequiredMiddleware",
    "core.middleware.CacheControlMiddleware",
    "core.middleware.RequestIDMiddleware",
    "control_room.middleware.PlatformRedirectMiddleware",
    "control_room.middleware.MaintenanceModeMiddleware",
]

# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "common.context_processors.site_settings",
                "common.context_processors.navigation",
                "common.context_processors.platform_extras",
            ],
        },
    },
]

# ---------------------------------------------------------------------------
# Database — PostgreSQL
# ---------------------------------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": env("DB_ENGINE", default="django.db.backends.postgresql"),
        "NAME": env("DB_NAME", default="enterprise_platform"),
        "USER": env("DB_USER", default="postgres"),
        "PASSWORD": env("DB_PASSWORD", default="postgres"),
        "HOST": env("DB_HOST", default="localhost"),
        "PORT": env("DB_PORT", default="5432"),
        "CONN_MAX_AGE": env.int("DB_CONN_MAX_AGE", default=600),
        "OPTIONS": {
            "connect_timeout": 10,
        },
    }
}

# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

AUTH_USER_MODEL = "accounts.User"

AUTHENTICATION_BACKENDS = [
    "accounts.backends.EnterpriseAuthBackend",
    "django.contrib.auth.backends.ModelBackend",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "customer_portal:dashboard"
LOGOUT_REDIRECT_URL = "accounts:logged_out"

# ---------------------------------------------------------------------------
# Internationalization
# ---------------------------------------------------------------------------

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ("en", "English"),
    ("fr", "French"),
    ("es", "Spanish"),
]

LOCALE_PATHS = [BASE_DIR / "locale"]

# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------

STATIC_URL = env("STATIC_URL", default="/static/")
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "static",
    BASE_DIR / "frontend" / "shared-ui" / "tokens",
]

STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# ---------------------------------------------------------------------------
# Media files
# ---------------------------------------------------------------------------

MEDIA_URL = env("MEDIA_URL", default="/media/")
MEDIA_ROOT = BASE_DIR / "media"

# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------

EMAIL_BACKEND = env(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)
EMAIL_HOST = env("EMAIL_HOST", default="localhost")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@example.com")

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

LOG_DIR = BASE_DIR / env("LOG_DIR", default="logs")
LOG_LEVEL = env("LOG_LEVEL", default="INFO")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {asctime} {name} {message}",
            "style": "{",
        },
        "request": {
            "format": "{levelname} {asctime} {name} request_id={request_id} {message}",
            "style": "{",
        },
    },
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
        "request_id": {
            "()": "core.logging.RequestIDFilter",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "filters": ["request_id"],
        },
        "file": {
            "level": LOG_LEVEL,
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "django.log",
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "verbose",
            "filters": ["request_id"],
        },
        "error_file": {
            "level": "ERROR",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "error.log",
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 10,
            "formatter": "verbose",
            "filters": ["request_id"],
        },
        "security_file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "security.log",
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 10,
            "formatter": "verbose",
            "filters": ["request_id"],
        },
        "mail_admins": {
            "level": "ERROR",
            "class": "django.utils.log.AdminEmailHandler",
            "filters": ["require_debug_false"],
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": LOG_LEVEL,
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "django.request": {
            "handlers": ["error_file", "mail_admins"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console", "file"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "security": {
            "handlers": ["console", "security_file"],
            "level": "INFO",
            "propagate": False,
        },
        "payments": {
            "handlers": ["console", "file"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
    },
}

# ---------------------------------------------------------------------------
# Security defaults (overridden in production)
# ---------------------------------------------------------------------------

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURITY_PERMISSIONS_POLICY = "camera=(), microphone=(), geolocation=(), payment=()"
SECURITY_CSP = {
    "default-src": ["'self'"],
    "base-uri": ["'self'"],
    "form-action": ["'self'"],
    "frame-ancestors": ["'none'"],
    "img-src": ["'self'", "data:", "https:"],
    "script-src": ["'self'", "'unsafe-inline'"],
    "style-src": ["'self'", "'unsafe-inline'"],
    "font-src": ["'self'", "data:"],
    "connect-src": ["'self'", "https://api.paystack.co", "https://api.flutterwave.com", "https://api.hubtel.com"],
    "object-src": ["'none'"],
}

# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------

SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14  # 2 weeks
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# Enterprise auth limits
AUTH_MAX_LOGIN_ATTEMPTS = 5
AUTH_LOCKOUT_MINUTES = 30
AUTH_LOGIN_RATE_LIMIT = 10
AUTH_LOGIN_RATE_WINDOW = 900

# ---------------------------------------------------------------------------
# Payments — gateway credentials via environment (never store secrets in DB)
# ---------------------------------------------------------------------------

PAYMENTS_DEFAULT_GATEWAY = env("PAYMENTS_DEFAULT_GATEWAY", default="paystack")

PAYMENTS_GATEWAYS = {
    "paystack": {
        "enabled": env.bool("PAYSTACK_ENABLED", default=False),
        "public_key": env("PAYSTACK_PUBLIC_KEY", default=""),
        "secret_key": env("PAYSTACK_SECRET_KEY", default=""),
        "webhook_secret": env("PAYSTACK_WEBHOOK_SECRET", default=""),
    },
    "hubtel": {
        "enabled": env.bool("HUBTEL_ENABLED", default=False),
        "client_id": env("HUBTEL_CLIENT_ID", default=""),
        "client_secret": env("HUBTEL_CLIENT_SECRET", default=""),
        "merchant_account_number": env("HUBTEL_MERCHANT_ACCOUNT", default=""),
        "webhook_secret": env("HUBTEL_WEBHOOK_SECRET", default=""),
    },
    "flutterwave": {
        "enabled": env.bool("FLUTTERWAVE_ENABLED", default=False),
        "public_key": env("FLUTTERWAVE_PUBLIC_KEY", default=""),
        "secret_key": env("FLUTTERWAVE_SECRET_KEY", default=""),
        "webhook_secret": env("FLUTTERWAVE_WEBHOOK_SECRET", default=""),
    },
    "manual": {
        "enabled": env.bool("MANUAL_PAYMENTS_ENABLED", default=True),
        "allowed_methods": ["bank_transfer", "cash", "cheque"],
    },
}

PAYSTACK_WEBHOOK_SECRET = env("PAYSTACK_WEBHOOK_SECRET", default="")
HUBTEL_WEBHOOK_SECRET = env("HUBTEL_WEBHOOK_SECRET", default="")
FLUTTERWAVE_WEBHOOK_SECRET = env("FLUTTERWAVE_WEBHOOK_SECRET", default="")

# ---------------------------------------------------------------------------
# Cache (Redis when REDIS_URL is set; local memory otherwise)
# ---------------------------------------------------------------------------

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "enterprise-platform",
    }
}

from config.redis_settings import apply_redis_settings  # noqa: E402

_redis_settings = apply_redis_settings(env)
if _redis_settings:
    CACHES = _redis_settings["CACHES"]  # noqa: F811
    SESSION_ENGINE = _redis_settings["SESSION_ENGINE"]
    SESSION_CACHE_ALIAS = _redis_settings["SESSION_CACHE_ALIAS"]

# ---------------------------------------------------------------------------
# Application-specific settings placeholders
# ---------------------------------------------------------------------------

CMS_PAGE_CACHE_TIMEOUT = 300
PRODUCTS_ITEMS_PER_PAGE = 12
BLOG_POSTS_PER_PAGE = 10

# ---------------------------------------------------------------------------
# SEO & social
# ---------------------------------------------------------------------------

SITE_DESCRIPTION = env(
    "SITE_DESCRIPTION",
    default="Enterprise software platform for modern teams — products, documentation, and customer success.",
)
SITE_DEFAULT_TITLE = env("SITE_DEFAULT_TITLE", default=SITE_NAME)
SEO_DEFAULT_OG_IMAGE = env("SEO_DEFAULT_OG_IMAGE", default="/static/images/og-default.svg")
SEO_LOGO_URL = env("SEO_LOGO_URL", default="/static/images/og-default.svg")
SEO_LOCALE = env("SEO_LOCALE", default="en_US")
SEO_TWITTER_HANDLE = env("SEO_TWITTER_HANDLE", default="")
SEO_SOCIAL_PROFILES = env.list("SEO_SOCIAL_PROFILES", default=[])
PUBLIC_PAGE_CACHE_SECONDS = CMS_PAGE_CACHE_TIMEOUT
