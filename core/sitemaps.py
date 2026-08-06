from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = "weekly"

    def items(self):
        return [
            "website:home",
            "pages:about",
            "products:list",
            "contact:form",
            "marketing:hub",
            "marketing:blog_list",
            "marketing:resources",
            "marketing:events",
            "marketing:success_stories",
            "marketing:case_studies",
            "marketing:whitepapers",
            "documentation:index",
        ]

    def location(self, item):
        return reverse(item)


class ProductSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.9

    def items(self):
        from products.models import Product

        return Product.objects.filter(is_published=True).order_by("-updated_at")

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()


class BlogPostSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        from marketing.models import BlogPost

        return BlogPost.objects.filter(is_published=True).order_by("-published_at")

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()


class CMSPageSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.6

    def items(self):
        from cms.models import CMSPage, PageType

        return CMSPage.objects.filter(is_published=True, page_type=PageType.CUSTOM).order_by("-updated_at")

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()
