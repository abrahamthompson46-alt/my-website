from django.test import TestCase
from django.urls import reverse

from accounts.models import AuditEventType, AuditLog
from products.models import Product, ProductCategory, ProductStatus
from website.services.outbound_links import annotate_intent_links, build_intent_url, build_tracked_intent_path


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

    def test_annotate_intent_links_use_tracked_paths(self):
        rows = annotate_intent_links([self.churchhub, self.coretrust])
        self.assertEqual(len(rows), 2)
        self.assertTrue(rows[0]["trial_url"].startswith("/go/churchhub/trial/"))
        self.assertTrue(rows[0]["demo_url"].startswith("/go/churchhub/demo/"))
        self.assertIn("src=homepage", rows[0]["trial_url"])
        self.assertEqual(rows[1]["trial_url"], "")
        self.assertTrue(rows[1]["demo_url"].startswith("/go/microfinance-core/demo/"))

    def test_tracked_path_helper(self):
        path = build_tracked_intent_path(self.churchhub, "trial", source="product_page")
        self.assertEqual(path, "/go/churchhub/trial/?src=product_page")

    def test_coretrust_trial_intent_coerced_to_demo(self):
        url = build_intent_url(self.coretrust, "trial")
        self.assertTrue(url.startswith("https://micro.zreta.com/request-demo/"))
        self.assertIn("utm_campaign=request_demo", url)
        self.assertIn("intent=demo", url)
        path = build_tracked_intent_path(self.coretrust, "trial", source="product_page")
        self.assertEqual(path, "/go/microfinance-core/demo/?src=product_page")


class OutboundIntentRedirectTests(TestCase):
    def setUp(self):
        category = ProductCategory.objects.create(name="Vertical", slug="vertical-go")
        self.product = Product.objects.create(
            name="ChurchHub",
            slug="churchhub",
            category=category,
            status=ProductStatus.GA,
            is_published=True,
            register_url="https://mychurch.zreta.com/apply/",
            external_app_url="https://mychurch.zreta.com/",
        )

    def test_redirect_logs_and_forwards(self):
        response = self.client.get(reverse("website:outbound_intent", kwargs={"slug": "churchhub", "intent": "trial"}) + "?src=homepage")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith("https://mychurch.zreta.com/apply/"))
        self.assertIn("utm_source=zreta", response["Location"])
        self.assertEqual(
            AuditLog.objects.filter(event_type=AuditEventType.OUTBOUND_INTENT_CLICK).count(),
            1,
        )
        event = AuditLog.objects.get(event_type=AuditEventType.OUTBOUND_INTENT_CLICK)
        self.assertEqual(event.metadata.get("product"), "churchhub")
        self.assertEqual(event.metadata.get("intent"), "trial")
        self.assertEqual(event.metadata.get("source"), "homepage")

    def test_coretrust_trial_path_redirects_as_demo(self):
        category = ProductCategory.objects.create(name="Vertical", slug="vertical-ct")
        Product.objects.create(
            name="CoreTrust",
            slug="microfinance-core",
            category=category,
            status=ProductStatus.GA,
            is_published=True,
            demo_url="https://micro.zreta.com/request-demo/",
            register_url="https://micro.zreta.com/apply/",
            external_app_url="https://micro.zreta.com/",
        )
        response = self.client.get(
            reverse("website:outbound_intent", kwargs={"slug": "microfinance-core", "intent": "trial"})
            + "?src=legacy"
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith("https://micro.zreta.com/request-demo/"))
        self.assertIn("intent=demo", response["Location"])
        self.assertIn("utm_campaign=request_demo", response["Location"])
        event = AuditLog.objects.get(event_type=AuditEventType.OUTBOUND_INTENT_CLICK)
        self.assertEqual(event.metadata.get("intent"), "demo")
        self.assertEqual(event.metadata.get("requested_intent"), "trial")


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
        self.assertIn("Start ChurchHub trial", content)
        self.assertIn("Request CoreTrust Demo", content)
        self.assertNotIn("Start on CoreTrust", content)
        self.assertIn("/go/churchhub/trial/", content)
        self.assertIn("/go/microfinance-core/demo/", content)
        self.assertNotIn("/go/microfinance-core/trial/", content)
        self.assertIn("product-intent-list", content)
