from django.test import RequestFactory, TestCase, override_settings

from common.services.public_rate_limit import (
    is_checkout_rate_limited,
    is_contact_rate_limited,
    is_newsletter_rate_limited,
)


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "public-rate-limit-tests",
        }
    }
)
class PublicRateLimitTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _request(self, path="/"):
        return self.factory.post(path, REMOTE_ADDR="203.0.113.10")

    def test_newsletter_rate_limit_blocks_after_threshold(self):
        request = self._request("/newsletter/")
        for _ in range(10):
            self.assertFalse(is_newsletter_rate_limited(request))
        self.assertTrue(is_newsletter_rate_limited(request))

    def test_contact_rate_limit_blocks_after_threshold(self):
        request = self._request("/contact/")
        for _ in range(5):
            self.assertFalse(is_contact_rate_limited(request))
        self.assertTrue(is_contact_rate_limited(request))

    def test_checkout_rate_limit_blocks_after_threshold(self):
        request = self._request("/app/payments/checkout/")
        for _ in range(15):
            self.assertFalse(is_checkout_rate_limited(request))
        self.assertTrue(is_checkout_rate_limited(request))

    def tearDown(self):
        from django.core.cache import cache

        cache.clear()
