from django.test import TestCase
from django.urls import reverse

from cms.models import NewsArticle, Testimonial
from products.models import Product, ProductCategory, ProductStatus
from website.services.homepage import (
    get_homepage_featured_products,
    should_show_home_news,
    should_show_home_testimonials,
)


class HomepageServiceTests(TestCase):
    def setUp(self):
        self.category = ProductCategory.objects.create(name="Vertical", slug="vertical")

    def _create_product(self, slug, *, sort_order, featured=True, status=ProductStatus.GA):
        return Product.objects.create(
            name=slug.replace("-", " ").title(),
            slug=slug,
            category=self.category,
            is_published=True,
            is_featured=featured,
            status=status,
            sort_order=sort_order,
        )

    def test_featured_products_respect_sort_order(self):
        erp = self._create_product("erp-suite", sort_order=1)
        churchhub = self._create_product("churchhub", sort_order=2)
        school = self._create_product("school-management", sort_order=3)

        featured = get_homepage_featured_products()
        self.assertEqual([product.slug for product in featured], ["erp-suite", "churchhub", "school-management"])

    def test_featured_products_exclude_coming_soon(self):
        self._create_product("churchhub", sort_order=1)
        self._create_product("retail-commerce", sort_order=2, status=ProductStatus.COMING_SOON)

        featured = get_homepage_featured_products()
        self.assertEqual(len(featured), 1)
        self.assertEqual(featured[0].slug, "churchhub")

    def test_should_hide_placeholder_testimonials(self):
        Testimonial.objects.create(
            quote="Great platform.",
            author_name="Sarah Okonkwo",
            author_role="CTO",
            company="Example Co",
            show_on_home=True,
            is_published=True,
        )
        self.assertFalse(should_show_home_testimonials(Testimonial.objects.all()))

    def test_should_show_real_testimonials(self):
        Testimonial.objects.create(
            quote="ChurchHub simplified our giving.",
            author_name="Pastor Kwame Mensah",
            author_role="Lead Pastor",
            company="Grace Chapel",
            show_on_home=True,
            is_published=True,
        )
        self.assertTrue(should_show_home_testimonials(Testimonial.objects.all()))

    def test_should_hide_placeholder_news(self):
        article = NewsArticle.objects.create(
            title="Enterprise Platform expands to 18 countries",
            slug="enterprise-platform-expands-18-countries",
            excerpt="Placeholder.",
            body="Placeholder.",
            is_published=True,
        )
        self.assertFalse(should_show_home_news([article]))

    def test_should_hide_soc2_seed_blog_post(self):
        from marketing.models import BlogPost, BlogCategory, Author

        author = Author.objects.create(full_name="Editor", slug="editor", is_published=True)
        category = BlogCategory.objects.create(name="Company", slug="company")
        post = BlogPost.objects.create(
            title="Enterprise Platform achieves SOC 2 Type II",
            slug="enterprise-platform-achieves-soc-2-type-ii",
            category=category,
            author=author,
            excerpt="Placeholder.",
            body="Placeholder.",
            is_published=True,
        )
        self.assertFalse(should_show_home_news([post]))


class HomepageViewTests(TestCase):
    def test_homepage_uses_honest_copy(self):
        response = self.client.get(reverse("website:home"))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertNotIn("2,500", content)
        self.assertNotIn("Trusted by industry leaders", content)
        self.assertNotIn("Modern software for faith communities", content)
        self.assertIn("Zreta", content)
        self.assertIn("Explore products", content)
        self.assertIn("home-trust", content)
        self.assertIn("home-hero__trust-strip", content)

    def test_homepage_hides_testimonials_without_verified_stories(self):
        Testimonial.objects.create(
            quote="Generic praise.",
            author_name="Rev. James Mwangi",
            author_role="Director",
            company="Sample Org",
            show_on_home=True,
            is_published=True,
        )
        response = self.client.get(reverse("website:home"))
        self.assertNotContains(response, "home-testimonials")
