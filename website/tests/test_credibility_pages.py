from django.test import TestCase
from django.urls import reverse

from products.models import Product, ProductCategory, ProductStatus


class CredibilityPagesTests(TestCase):
    def setUp(self):
        category = ProductCategory.objects.create(name="Vertical", slug="vertical")
        Product.objects.create(
            name="ChurchHub",
            slug="churchhub",
            category=category,
            is_published=True,
            status=ProductStatus.GA,
            tagline="Faith communities",
            short_description="Membership and giving.",
        )
        Product.objects.create(
            name="CoreTrust",
            slug="microfinance-core",
            category=category,
            is_published=True,
            status=ProductStatus.GA,
            tagline="Microfinance",
            short_description="Loans and savings.",
        )

    def test_solution_landings(self):
        for name in (
            "website:solution_churches",
            "website:solution_microfinance",
            "website:solution_enterprises",
            "website:solution_education",
            "website:solution_healthcare",
        ):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200, name)

    def test_platform_pages(self):
        for name in (
            "website:architecture",
            "website:payments_platform",
            "website:integrations",
            "website:sla",
            "website:onboarding",
            "website:privacy_center",
            "website:continuity",
            "website:security",
            "website:status",
            "support:index",
            "pages:about",
        ):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200, name)

    def test_security_center_links_hub(self):
        response = self.client.get(reverse("website:security"))
        content = response.content.decode()
        self.assertIn("Security Center", content)
        self.assertIn("Privacy Center", content)
        self.assertNotIn("SOC 2 Type II", content)

    def test_about_hides_placeholder_team(self):
        from cms.models import TeamMember

        TeamMember.objects.create(
            full_name="Sarah Okonkwo",
            role="CEO",
            is_published=True,
            show_on_about=True,
        )
        response = self.client.get(reverse("pages:about"))
        self.assertNotContains(response, "Sarah Okonkwo")
        self.assertContains(response, "Company facts")

    def test_status_lists_external_products(self):
        response = self.client.get(reverse("website:status"))
        content = response.content.decode()
        self.assertIn("ChurchHub", content)
        self.assertIn("CoreTrust", content)
        self.assertIn("External product", content)

    def test_churches_solution_marks_live(self):
        response = self.client.get(reverse("website:solution_churches"))
        self.assertContains(response, "Live product")
        self.assertContains(response, "ChurchHub")

    def test_empty_case_studies_redirect_to_resources(self):
        response = self.client.get(reverse("marketing:case_studies"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("marketing:hub"))

    def test_empty_success_stories_redirect_to_resources(self):
        response = self.client.get(reverse("marketing:success_stories"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("marketing:hub"))


class ProductDepthTests(TestCase):
    def setUp(self):
        category = ProductCategory.objects.create(name="Vertical", slug="vertical")
        self.product = Product.objects.create(
            name="CoreTrust",
            slug="microfinance-core",
            category=category,
            is_published=True,
            status=ProductStatus.GA,
            short_description="Microfinance platform.",
        )

    def test_coretrust_detail_has_depth(self):
        response = self.client.get(reverse("products:detail", kwargs={"slug": "microfinance-core"}))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("How this product fits Zreta", content)
        self.assertIn("Loan lifecycle", content)
        self.assertIn("Live product application", content)
        self.assertNotIn("Instant account setup", content)
