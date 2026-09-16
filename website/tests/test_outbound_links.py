from django.test import TestCase
from django.urls import reverse

from products.models import Product, ProductCategory, ProductStatus
from website.services.outbound_links import annotate_intent_links, build_intent_url


class OutboundLinkTests(TestCase):
    def setUp(self):
        self.category = ProductCategory.objects.create(name="Vertical", slug="vertical-out")
        self.churchhub = Product.objects.create(
            name="ChurchHub",
            slug="churchhub",
            category=self.category,
            status=ProductStatus.GA,
            is_published=True,
            is_featured=True,
            sort_order=1,
            demo_url="https://mychurch.zreta.com/contact/",
            register_url="https://mychurch.zreta.com/apply/",
            external_app_url="https://mychurch.zreta.com/",
        )
        self.coretrust = Product.objects.create(
            name="CoreTrust",
            slug="microfinance-core",
            category=self.category,
            status=ProductStatus.GA,
            is_published=True,
            is_featured=True,
            sort_order=2,
            demo_url="https://micro.zreta.com/request-demo/",
            register_url="https://micro.zreta.com/request-demo/",
            external_app_url="https://micro.zreta.com/",
        )

    def test_trial_url_uses_register_and_tracking(self):
        url = build_intent_url(self.churchhub, "trial")
        self.assertTrue(url.startswith("https://mychurch.zreta.com/apply/"))
        self.assertIn("utm_source=zreta", url)
        self.assertIn("utm_campaign=start_trial", url)
        self.assertIn("intent=trial", url)
        self.assertIn("product=churchhub", url)

    def test_demo_url_uses_demo_and_tracking(self):
        url = build_intent_url(self.coretrust, "demo")
        self.assertTrue(url.startswith("https://micro.zreta.com/request-demo/"))
        self.assertIn("utm_campaign=request_demo", url)
        self.assertIn("intent=demo", url)

    def test_annotate_intent_links(self):
        rows = annotate_intent_links([self.churchhub, self.coretrust])
        self.assertEqual(len(rows), 2)
        self.assertTrue(rows[0]["trial_url"])
        self.assertTrue(rows[0]["demo_url"])


class HomepageIntentViewTests(TestCase):
    def setUp(self):
        from django.core.cache import cache

        cache.clear()
        category = ProductCategory.objects.create(name="Vertical", slug="vertical-home")
        Product.objects.create(
            name="ChurchHub",
            slug="churchhub",
            category=category,
            status=ProductStatus.GA,
            is_published=True,
            is_featured=True,
            demo_url="https://mychurch.zreta.com/contact/",
            register_url="https://mychurch.zreta.com/apply/",
            external_app_url="https://mychurch.zreta.com/",
        )
        Product.objects.create(
            name="CoreTrust",
            slug="microfinance-core",
            category=category,
            status=ProductStatus.GA,
            is_published=True,
            is_featured=True,
            demo_url="https://micro.zreta.com/request-demo/",
            register_url="https://micro.zreta.com/request-demo/",
            external_app_url="https://micro.zreta.com/",
        )

    def test_homepage_shows_product_intent_choosers(self):
        response = self.client.get(reverse("website:home"))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('id="start-trial"', content)
        self.assertIn('id="request-demo"', content)
        self.assertIn("Start on ChurchHub", content)
        self.assertIn("Demo CoreTrust", content)
        self.assertIn("mychurch.zreta.com/apply/", content)
        self.assertIn("micro.zreta.com/request-demo/", content)
        self.assertIn("utm_source=zreta", content)
        self.assertIn("product-intent-list", content)
