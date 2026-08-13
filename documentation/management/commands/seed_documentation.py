"""
Seed enterprise documentation content.
Usage: python manage.py seed_documentation
"""
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from documentation.models import DocArticle, DocCategory, DocDownload, DocVideo
from products.models import Product


class Command(BaseCommand):
    help = "Seed documentation categories, articles, videos, API endpoints, and downloads."

    @transaction.atomic
    def handle(self, *args, **options):
        if DocCategory.objects.exists():
            self.stdout.write(self.style.WARNING("Documentation already seeded. Skipping."))
            return

        products = list(Product.objects.filter(is_published=True).order_by("sort_order")[:3])
        if not products:
            self.stdout.write(self.style.ERROR("No products found. Run seed_products first."))
            return

        now = timezone.now()

        platform = DocCategory.objects.create(
            name="Platform",
            slug="platform",
            description="Core platform concepts for the Zreta marketing site, customer portal, and billing.",
            icon="layers",
            sort_order=1,
        )
        roadmap = DocCategory.objects.create(
            name="Roadmap",
            slug="roadmap",
            description="Planned integrations and future platform capabilities.",
            icon="map",
            sort_order=2,
        )

        product_cats = {}
        for i, product in enumerate(products):
            product_cats[product.slug] = DocCategory.objects.create(
                name=product.name,
                slug=f"product-{product.slug}",
                description=f"Documentation for {product.name}.",
                icon="package",
                sort_order=10 + i,
                product=product,
            )

        getting_started = [
            (
                "Welcome to Zreta",
                "Overview of the public website, customer portal, subscriptions, and support.",
                "getting_started",
            ),
            (
                "Quick start guide",
                "Create your account, verify email, start a trial, and access the customer portal.",
                "getting_started",
            ),
            (
                "Current platform scope",
                "What is live today: marketing site, customer portal, subscription billing, and staff control room.",
                "getting_started",
            ),
        ]
        for i, (title, excerpt, atype) in enumerate(getting_started):
            DocArticle.objects.create(
                category=platform,
                title=title,
                slug=f"platform-{title.lower().replace(' ', '-')[:40]}",
                article_type=atype,
                excerpt=excerpt,
                body=f"{excerpt}\n\nRefer to docs/ZRETA_SCOPE_TRUTH.md in the repository for the authoritative capability matrix.",
                is_published=True,
                is_featured=i == 0,
                sort_order=i,
                published_at=now,
            )

        install_guides = [
            ("System requirements", "Supported browsers and recommended infrastructure for deploying this Django site."),
            ("Production deployment", "Deploy with PostgreSQL, Redis, Gunicorn, and Nginx using the included deploy/ templates."),
            ("Environment configuration", "Configure SMTP, payment gateways, and site URLs via environment variables."),
            ("Database setup", "Configure PostgreSQL, backups, and connection pooling."),
        ]
        for i, (title, body) in enumerate(install_guides):
            DocArticle.objects.create(
                category=platform,
                title=title,
                slug=f"install-{title.lower().replace(' ', '-')[:40]}",
                article_type="installation",
                excerpt=body[:120],
                body=body,
                is_published=True,
                sort_order=i,
                published_at=now,
            )

        faqs = [
            ("How do I reset my password?", "Use the forgot password link on the login page or contact your administrator."),
            ("What browsers are supported?", "Latest versions of Chrome, Firefox, Safari, and Edge are fully supported."),
            ("Is there a public REST API today?", "Not yet. Programmatic integration is on the roadmap. See the Roadmap category."),
            ("How is data backed up?", "Configure PostgreSQL and media backups as part of your production deployment."),
        ]
        for i, (question, answer) in enumerate(faqs):
            DocArticle.objects.create(
                category=platform,
                title=question,
                slug=f"faq-{i + 1}",
                article_type="faq",
                body=answer,
                is_published=True,
                sort_order=i,
                published_at=now,
            )

        DocArticle.objects.create(
            category=roadmap,
            title="REST API (planned)",
            slug="roadmap-rest-api",
            article_type="roadmap",
            excerpt="A versioned HTTP API for integrations is planned but not implemented in the current codebase.",
            body=(
                "The current application is a Django monolith with server-rendered pages.\n\n"
                "Future `/api/v1/` endpoints described in earlier drafts are roadmap items only."
            ),
            is_published=True,
            is_featured=True,
            published_at=now,
        )

        DocArticle.objects.create(
            category=roadmap,
            title="Multi-tenant organization workspaces (planned)",
            slug="roadmap-multi-tenancy",
            article_type="roadmap",
            excerpt="Organization-level data isolation is planned for future modular products.",
            body=(
                "Today, customer portal data is isolated per user account.\n\n"
                "Shared organization/tenant workspaces are not implemented yet."
            ),
            is_published=True,
            published_at=now,
        )

        DocArticle.objects.create(
            category=roadmap,
            title="Microfinance Core banking modules (planned)",
            slug="roadmap-microfinance-core",
            article_type="roadmap",
            excerpt="Loans, savings, ledger, and core banking workflows are product roadmap items.",
            body=(
                "Microfinance Core is positioned as a future modular product.\n\n"
                "The current repository implements marketing pages, subscription billing, and payment collection only."
            ),
            is_published=True,
            published_at=now,
        )

        for product in products:
            cat = product_cats[product.slug]
            DocArticle.objects.create(
                category=cat,
                product=product,
                title=f"{product.name} — product overview",
                slug=f"{product.slug}-overview",
                article_type="guide",
                excerpt="Product positioning, current availability, and links to live demos where applicable.",
                body="See the product detail page for current status (Generally Available, Beta, or Coming Soon).",
                is_published=True,
                published_at=now,
            )
            DocVideo.objects.create(
                category=cat,
                product=product,
                title=f"{product.name} product tour",
                description="A walkthrough of key features and workflows.",
                video_url="https://example.com/videos/tour",
                duration_minutes=10,
                sort_order=0,
            )
            DocDownload.objects.create(
                category=cat,
                product=product,
                title=f"{product.name} Admin Guide (PDF)",
                description="Administrator reference manual.",
                file_type="pdf",
                version="1.0",
                file=ContentFile(b"PDF placeholder", name=f"{product.slug}-admin-guide.pdf"),
            )

        self.stdout.write(self.style.SUCCESS("Documentation seeded successfully."))
