from django.test import Client, TestCase, override_settings
from django.urls import reverse


class SecurityHeadersTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_homepage_csp_blocks_inline_scripts(self):
        response = self.client.get(reverse("website:home"))
        self.assertEqual(response.status_code, 200)
        csp = response["Content-Security-Policy"]
        self.assertIn("script-src 'self'", csp)
        self.assertNotIn("script-src 'self' 'unsafe-inline'", csp)
        self.assertNotIn("'unsafe-inline'", csp.split("script-src")[1].split(";")[0])
        self.assertIn("frame-ancestors 'none'", csp)
        self.assertEqual(response["X-Frame-Options"], "DENY")
