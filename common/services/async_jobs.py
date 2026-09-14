"""Helpers for running work inline or via Celery."""

from __future__ import annotations

import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def celery_async_enabled() -> bool:
    """Return True when tasks should be queued to a worker."""
    if getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False):
        return False
    broker = (getattr(settings, "CELERY_BROKER_URL", "") or "").strip()
    if not broker or broker.startswith("memory://"):
        return False
    return True


def dispatch_task(task, *args, **kwargs):
    """
    Queue ``task`` when Celery async mode is enabled; otherwise run inline.

    Returns the AsyncResult when queued, or the task return value when inline.
    """
    if celery_async_enabled():
        return task.delay(*args, **kwargs)
    return task.apply(args=args, kwargs=kwargs).get()
