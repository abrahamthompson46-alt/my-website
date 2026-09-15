"""Django project configuration package."""

try:
    from .celery import app as celery_app
except ModuleNotFoundError:  # pragma: no cover - deploy without celery installed yet
    celery_app = None

__all__ = ("celery_app",)
