"""Prometheus metrics helpers for Zreta observability."""

from __future__ import annotations

import time

from django.conf import settings
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

HTTP_REQUESTS = Counter(
    "zreta_http_requests_total",
    "HTTP requests handled by Django",
    ["method", "status"],
)
HTTP_REQUEST_DURATION = Histogram(
    "zreta_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)
WEBHOOK_EVENTS = Counter(
    "zreta_webhook_events_total",
    "Payment webhook outcomes",
    ["gateway", "result"],
)
EMAIL_EVENTS = Counter(
    "zreta_email_events_total",
    "Outbound platform email outcomes",
    ["result"],
)

_SKIP_PREFIXES = (
    "/static/",
    "/media/",
    "/metrics",
    "/health/",
    "/favicon.ico",
)


def metrics_enabled() -> bool:
    return bool(getattr(settings, "METRICS_ENABLED", False))


def should_skip_path(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in _SKIP_PREFIXES)


def observe_http_request(*, method: str, status_code: int, duration_seconds: float) -> None:
    if not metrics_enabled():
        return
    HTTP_REQUESTS.labels(method=method.upper(), status=str(status_code)).inc()
    HTTP_REQUEST_DURATION.labels(method=method.upper()).observe(duration_seconds)


def observe_webhook(*, gateway: str, result: str) -> None:
    if not metrics_enabled():
        return
    WEBHOOK_EVENTS.labels(gateway=gateway or "unknown", result=result).inc()


def observe_email(*, result: str) -> None:
    if not metrics_enabled():
        return
    EMAIL_EVENTS.labels(result=result).inc()


def render_metrics() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST


class Timer:
    def __init__(self):
        self._start = time.perf_counter()

    def seconds(self) -> float:
        return time.perf_counter() - self._start
