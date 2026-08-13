from django.http import Http404
from django.test import SimpleTestCase, override_settings
from django.urls import resolve


class MediaUrlTests(SimpleTestCase):
    def test_local_media_route_is_registered_in_production_mode(self):
        with override_settings(DEBUG=False):
            match = resolve("/media/products/screenshots/example.png")
            self.assertEqual(match.func.__name__, "_serve_public_media")
            self.assertEqual(match.kwargs["path"], "products/screenshots/example.png")

    def test_private_media_route_is_registered_in_production_mode(self):
        with override_settings(DEBUG=False):
            match = resolve("/media/private/payments/proofs/example.pdf")
            self.assertEqual(match.func.__name__, "_serve_public_media")
            self.assertEqual(match.kwargs["path"], "private/payments/proofs/example.pdf")
