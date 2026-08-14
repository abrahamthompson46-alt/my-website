"""
Seed marketing CMS content.
Usage: python manage.py seed_marketing
"""
from datetime import timedelta

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify
from django.utils import timezone

from marketing.models import (
    Author,
    BlogCategory,
    BlogPost,
    BlogTag,
    CaseStudy,
    MarketingEvent,
    MarketingResource,
    SuccessStory,
    WhitePaper,
)
from products.models import Product


class Command(BaseCommand):
    help = "Seed marketing blog, events, stories, case studies, whitepapers, and resources."

    @transaction.atomic
    def handle(self, *args, **options):
        if BlogPost.objects.exists():
            self.stdout.write(self.style.WARNING("Marketing content already exists. Skipping."))
            return

        now = timezone.now()
        products = list(Product.objects.filter(is_published=True).order_by("sort_order")[:3])
        product = products[0] if products else None

        author = Author.objects.create(
            full_name="Sarah Okonkwo",
            slug="sarah-okonkwo",
            role="Head of Product Marketing",
            bio="Sarah leads product marketing and customer storytelling at Zreta.",
            is_published=True,
        )

        categories = {
            "updates": BlogCategory.objects.create(name="Product Updates", slug="product-updates", sort_order=1),
            "guides": BlogCategory.objects.create(name="Guides", slug="guides", sort_order=2),
            "company": BlogCategory.objects.create(name="Company", slug="company", sort_order=3),
        }

        tags = {}
        for name, slug in [("SaaS", "saas"), ("Enterprise", "enterprise"), ("Security", "security")]:
            tags[name] = BlogTag.objects.create(name=name, slug=slug)

        posts = [
            ("Introducing Hospital Management 2.0", "updates", "New patient timeline, lab integrations, and billing automation.", True),
            ("How to scale microfinance operations", "guides", "A practical framework for cloud-native core banking migration.", False),
            ("How Zreta approaches platform security", "company", "An overview of authentication, audit logging, and operational controls.", False),
        ]
        for i, (title, cat_key, excerpt, featured) in enumerate(posts):
            post = BlogPost.objects.create(
                title=title,
                slug=slugify(title)[:80],
                category=categories[cat_key],
                author=author,
                excerpt=excerpt,
                body=f"{excerpt}\n\nRead the full article for detailed guidance and best practices.",
                read_time_minutes=4 + i,
                is_featured=featured,
                is_published=True,
                published_at=now - timedelta(days=7 - i),
                meta_title=title,
                meta_description=excerpt,
            )
            post.tags.set([tags["SaaS"], tags["Enterprise"]])

        MarketingEvent.objects.create(
            title="Zreta Live Demo",
            slug="zreta-live-demo",
            event_type="webinar",
            excerpt="See Zreta products in a live 45-minute demo with Q&A.",
            body="Join our product specialists for a comprehensive walkthrough.",
            starts_at=now + timedelta(days=14),
            ends_at=now + timedelta(days=14, hours=1),
            registration_url="https://example.com/register",
            is_featured=True,
            is_published=True,
        )

        SuccessStory.objects.create(
            title="Unity Microfinance saves 20 hours per week",
            slug="unity-microfinance-success",
            company="Unity Microfinance",
            industry="Financial Services",
            quote="We consolidated five legacy systems into one platform.",
            excerpt="How Unity Microfinance streamlined operations across branches.",
            body="Unity Microfinance deployed Microfinance Core across 12 branches with full regulatory reporting.",
            result_metric="20 hours saved weekly on reporting",
            product=products[1] if len(products) > 1 else product,
            is_featured=True,
            is_published=True,
        )

        CaseStudy.objects.create(
            title="Horizon Academy digitizes fee collection",
            slug="horizon-academy-case-study",
            client_name="Horizon Academy",
            industry="Education",
            challenge="Manual fee tracking caused delays and reconciliation errors.",
            solution="Deployed School Management with parent portal and mobile payments.",
            results="60% reduction in fee collection delays within one term.",
            excerpt="Horizon Academy transformed fee operations with School Management.",
            body="Full implementation across 2,000 students in under 8 weeks.",
            product=products[2] if len(products) > 2 else product,
            is_featured=True,
            is_published=True,
        )

        WhitePaper.objects.create(
            title="The Future of Enterprise SaaS in Africa",
            slug="future-enterprise-saas-africa",
            excerpt="Research on adoption trends, compliance, and modular platform strategies.",
            body="This white paper explores how organizations are modernizing with cloud-native platforms.",
            is_gated=True,
            is_featured=True,
            is_published=True,
            file=ContentFile(b"White paper placeholder", name="future-enterprise-saas.pdf"),
        )

        MarketingResource.objects.create(
            title="ERP Implementation Checklist",
            slug="erp-implementation-checklist",
            resource_type="checklist",
            description="Step-by-step checklist for ERP rollout planning.",
            file=ContentFile(b"Checklist placeholder", name="erp-checklist.pdf"),
            is_featured=True,
            is_published=True,
        )
        MarketingResource.objects.create(
            title="Security Best Practices Guide",
            slug="security-best-practices",
            resource_type="guide",
            description="Enterprise security configuration recommendations.",
            external_url="https://example.com/security-guide",
            is_published=True,
        )

        self.stdout.write(self.style.SUCCESS("Marketing content seeded successfully."))
