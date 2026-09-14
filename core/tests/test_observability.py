"""Observability tests: structured logging and Prometheus metrics."""

import json
import logging

from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from core.logging import JsonFormatter, RequestIDFilter, reset_request_id, set_request_id
from core.metrics import observe_email, observe_http_request, observe_webhook, render_metrics


class JsonLoggingTests(SimpleTestCase):
    def test_json_formatter_includes_request_id(self):
        token = set_request_id("req-123")
        try:
            record = logging.LogRecord(
                name="test.logger",
                level=logging.INFO,
                pathname=__file__,
                lineno=1,
                msg="hello %s",
                args=("world",),
                exc_info=None,
            )
            RequestIDFilter().filter(record)
            payload = json.loads(JsonFormatter().format(record))
        finally:
            reset_request_id(token)

        self.assertEqual(payload["message"], "hello world")
        self.assertEqual(payload["request_id"], "req-123")
        self.assertEqual(payload["level"], "INFO")
        self.assertEqual(payload["logger"], "test.logger")
        self.assertIn("timestamp", payload)


@override_settings(
    ALLOWED_HOSTS=["testserver"],
    SECURE_SSL_REDIRECT=False,
    METRICS_ENABLED=True,
    METRICS_TOKEN="test-metrics-token",
)
class MetricsEndpointTests(TestCase):
    def test_metrics_requires_token(self):
        response = self.client.get(reverse("metrics"))
        self.assertEqual(response.status_code, 401)

    def test_metrics_accepts_bearer_token(self):
        observe_http_request(method="GET", status_code=200, duration_seconds=0.01)
        observe_webhook(gateway="paystack", result="processed")
        observe_email(result="sent")

        response = self.client.get(
            reverse("metrics"),
            HTTP_AUTHORIZATION="Bearer test-metrics-token",
        )
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        self.assertIn("zreta_http_requests_total", body)
        self.assertIn("zreta_webhook_events_total", body)
        self.assertIn("zreta_email_events_total", body)
        self.assertIn("text/plain", response["Content-Type"])

    def test_metrics_accepts_query_token(self):
        response = self.client.get(reverse("metrics"), {"token": "test-metrics-token"})
        self.assertEqual(response.status_code, 200)

    @override_settings(METRICS_ENABLED=False)
    def test_metrics_disabled_returns_404(self):
        response = self.client.get(
            reverse("metrics"),
            HTTP_AUTHORIZATION="Bearer test-metrics-token",
        )
        self.assertEqual(response.status_code, 404)

    def test_request_id_header_roundtrip(self):
        response = self.client.get(reverse("health_check"), HTTP_X_REQUEST_ID="fixed-id-9")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["X-Request-ID"], "fixed-id-9")

    def test_render_metrics_bytes(self):
        body, content_type = render_metrics()
        self.assertIsInstance(body, (bytes, bytearray))
        self.assertIn("text/plain", content_type)
