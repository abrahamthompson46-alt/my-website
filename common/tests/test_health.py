from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse


@override_settings(
    ALLOWED_HOSTS=["testserver"],
    SECURE_SSL_REDIRECT=False,
)
class HealthCheckTests(TestCase):
    def test_health_returns_ok(self):
        response = self.client.get(reverse("health_check"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["checks"]["database"], "ok")
        self.assertIn(data["checks"]["cache_backend"], {"locmem", "redis"})

    @patch("core.views.connection")
    def test_health_hides_database_errors(self, mock_connection):
        mock_connection.cursor.side_effect = Exception("connection refused: secret-host")
        response = self.client.get(reverse("health_check"))
        self.assertEqual(response.status_code, 503)
        data = response.json()
        self.assertEqual(data["status"], "error")
        self.assertEqual(data["checks"]["database"], "unavailable")
        self.assertNotIn("secret-host", response.content.decode())
