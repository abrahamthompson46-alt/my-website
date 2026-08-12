from django.test import SimpleTestCase, override_settings
from django.urls import resolve


class MediaUrlTests(SimpleTestCase):
    def test_local_media_route_is_registered_in_production_mode(self):
        with override_settings(DEBUG=False):
            match = resolve("/media/products/screenshots/example.png")
            self.assertEqual(match.func.__name__, "serve")
            self.assertEqual(match.kwargs["path"], "products/screenshots/example.png")
