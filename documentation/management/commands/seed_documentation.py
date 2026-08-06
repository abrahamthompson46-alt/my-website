"""
Seed enterprise documentation content.
Usage: python manage.py seed_documentation
"""
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from documentation.models import DocAPIEndpoint, DocArticle, DocCategory, DocDownload, DocVideo
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
            description="Core platform concepts, architecture, and shared services.",
            icon="layers",
            sort_order=1,
        )
        api_cat = DocCategory.objects.create(
            name="REST API",
            slug="rest-api",
            description="HTTP API endpoints for programmatic integration.",
            icon="code",
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
            ("Welcome to the platform", "Overview of modules, deployment models, and key concepts.", "getting_started"),
            ("Quick start guide", "Create your account, invite team members, and configure your first workspace.", "getting_started"),
            ("Architecture overview", "Understand multi-tenant design, data isolation, and integration points.", "getting_started"),
        ]
        for i, (title, excerpt, atype) in enumerate(getting_started):
            DocArticle.objects.create(
                category=platform,
                title=title,
                slug=f"platform-{title.lower().replace(' ', '-')[:40]}",
                article_type=atype,
                excerpt=excerpt,
                body=f"{excerpt}\n\nThis guide walks through the essential steps to get started with the enterprise platform.",
                is_published=True,
                is_featured=i == 0,
                sort_order=i,
                published_at=now,
            )

        install_guides = [
            ("System requirements", "Hardware, OS, and network prerequisites for on-premise and cloud deployments."),
            ("Cloud deployment", "Deploy to AWS, Azure, or GCP using our infrastructure templates."),
            ("On-premise installation", "Step-by-step installation for air-gapped and private data center environments."),
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
            ("Is offline mode available?", "Selected modules support offline sync for field operations."),
            ("How is data backed up?", "Automated daily backups with configurable retention and point-in-time recovery."),
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
            category=api_cat,
            title="Authentication",
            slug="api-authentication",
            article_type="api",
            excerpt="Authenticate API requests using bearer tokens and API keys.",
            body="All API requests require a valid bearer token in the Authorization header.\n\nExample: Authorization: Bearer <token>",
            is_published=True,
            is_featured=True,
            published_at=now,
        )

        endpoints = [
            ("List users", "GET", "/api/v1/users", "Returns a paginated list of users in the organization."),
            ("Create user", "POST", "/api/v1/users", "Creates a new user account."),
            ("Get subscription", "GET", "/api/v1/subscriptions/{id}", "Retrieves subscription details by ID."),
            ("List invoices", "GET", "/api/v1/invoices", "Returns billing invoices for the authenticated account."),
        ]
        for i, (name, method, path, summary) in enumerate(endpoints):
            DocAPIEndpoint.objects.create(
                category=api_cat,
                name=name,
                method=method,
                path=path,
                summary=summary,
                description=f"{summary} Refer to the authentication guide for required headers.",
                request_example='curl -H "Authorization: Bearer $TOKEN" https://api.example.com' + path.replace("{id}", "123"),
                response_example='{"data": [], "meta": {"page": 1, "total": 0}}',
                sort_order=i,
            )

        for product in products:
            cat = product_cats[product.slug]
            DocArticle.objects.create(
                category=cat,
                product=product,
                title=f"{product.name} — Release notes v2.1.0",
                slug=f"{product.slug}-release-2-1-0",
                article_type="release_note",
                version="2.1.0",
                excerpt="Performance improvements, new dashboard widgets, and bug fixes.",
                body="This release includes enhanced reporting, improved mobile responsiveness, and security patches.",
                is_published=True,
                published_at=now,
            )
            DocVideo.objects.create(
                category=cat,
                product=product,
                title=f"{product.name} product tour",
                description="A 10-minute walkthrough of key features and workflows.",
                video_url="https://example.com/videos/tour",
                duration_minutes=10,
                sort_order=0,
            )
            DocDownload.objects.create(
                category=cat,
                product=product,
                title=f"{product.name} Admin Guide (PDF)",
                description="Complete administrator reference manual.",
                file_type="pdf",
                version="2.1",
                file=ContentFile(b"PDF placeholder", name=f"{product.slug}-admin-guide.pdf"),
            )

        self.stdout.write(self.style.SUCCESS("Documentation seeded successfully."))
