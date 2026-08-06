from unittest.mock import patch

from django.test import TestCase, override_settings

from control_room.services.cache_health import get_cache_diagnostics, mask_redis_url, probe_cache


class CacheHealthTests(TestCase):
    def test_mask_redis_url_hides_credentials(self):
        masked = mask_redis_url("redis://:secret@localhost:6379/0")
        self.assertEqual(masked, "redis://localhost:6379/0")
        self.assertNotIn("secret", masked)

    def test_probe_cache_round_trip(self):
        result = probe_cache()
        self.assertTrue(result["ok"])
        self.assertIsNotNone(result["latency_ms"])

    @override_settings(
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "test-cache-health",
            }
        },
        SESSION_ENGINE="django.contrib.sessions.backends.db",
    )
    def test_get_cache_diagnostics_locmem(self):
        diagnostics = get_cache_diagnostics()
        self.assertEqual(diagnostics["backend"], "locmem")
        self.assertFalse(diagnostics["redis_active"])
        self.assertIn("REDIS_URL", diagnostics["recommendation"])
        self.assertTrue(diagnostics["probe"]["ok"])

    @override_settings(
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "test-cache-health-redis-label",
            }
        },
        SESSION_ENGINE="django.contrib.sessions.backends.cache",
    )
    @patch("control_room.services.cache_health.get_cache_backend_label", return_value="redis")
    @patch("control_room.services.cache_health.get_redis_server_info", return_value={"version": "7.0", "used_memory_human": "1M", "connected_clients": 1, "uptime_days": 1})
    def test_get_cache_diagnostics_redis(self, _mock_info, _mock_label):
        diagnostics = get_cache_diagnostics()
        self.assertEqual(diagnostics["backend"], "redis")
        self.assertTrue(diagnostics["redis_active"])
        self.assertTrue(diagnostics["sessions_use_cache"])
