"""
Sync homepage CMS content to the current honest marketing baseline.

Usage:
    python manage.py sync_homepage
    python manage.py sync_homepage --products
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from cms.models import CMSPage, HeroBanner, NewsArticle, PageSection, PageType, SectionItem, Testimonial
from products.models import Product, ProductStatus
from website.content import (
    CTA,
    HERO,
    INDUSTRIES,
    NEWSLETTER,
    REQUEST_DEMO,
    STATISTICS,
    TRUST_SIGNALS,
    WHY_CHOOSE_US,
)


class Command(BaseCommand):
    help = "Refresh homepage hero, sections, stats, and trust signals from the canonical content baseline."

    def add_arguments(self, parser):
        parser.add_argument(
            "--products",
            action="store_true",
            help="Also normalize homepage featured flags (ChurchHub-first, hide coming-soon from featured).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        page = CMSPage.objects.filter(page_type=PageType.HOME).first()
        if not page:
            self.stdout.write(self.style.WARNING("No home CMS page found. Run seed_cms first."))
            return

        hero = page.hero
        if hero:
            hero.eyebrow = HERO["eyebrow"]
            hero.headline = HERO["headline"]
            hero.subheadline = HERO["subheadline"]
            hero.trust_text = HERO["trust_text"]
            hero.cta_primary_label = HERO.get("cta_primary_label", "Start ChurchHub trial")
            hero.cta_secondary_label = HERO.get("cta_secondary_label", "Request a Demo")
            hero.cta_secondary_url = "#request-demo"
            hero.is_active = True
            hero.save()

        page.meta_title = "ChurchHub & modular enterprise software"
        page.meta_description = (
            "ChurchHub for faith communities — members, giving, events, and communications. "
            "Built on Zreta with GHS pricing, Mobile Money, and enterprise security."
        )
        page.save(update_fields=["meta_title", "meta_description", "updated_at"])

        self._sync_section(page, "why_choose_us", WHY_CHOOSE_US, item_factory=self._why_item)
        self._sync_section(page, "industries", INDUSTRIES, item_factory=self._industry_item)
        self._sync_section(page, "statistics", STATISTICS, item_factory=self._stat_item)
        self._sync_section(page, "trust_signals", TRUST_SIGNALS, item_factory=self._trust_item)

        self._sync_header(page, "cta", CTA["title"], CTA["subtitle"])
        self._sync_header(
            page,
            "request_demo",
            REQUEST_DEMO["title"],
            REQUEST_DEMO["subtitle"],
            eyebrow=REQUEST_DEMO["eyebrow"],
        )
        self._sync_header(page, "newsletter", NEWSLETTER["title"], NEWSLETTER["subtitle"])

        demo_section = self._get_or_create_section(page, "request_demo", sort_order=8)
        demo_section.items.all().delete()
        for i, (title, icon) in enumerate(
            [
                ("30-minute tailored demo", "check-circle"),
                ("Q&A with product specialists", "check-circle"),
                ("GHS pricing overview", "check-circle"),
                ("No commitment required", "check-circle"),
            ]
        ):
            SectionItem.objects.create(section=demo_section, title=title, icon=icon, sort_order=i, is_active=True)

        partner_section = PageSection.objects.filter(page=page, section_key="partner_logos").first()
        if partner_section:
            partner_section.is_active = False
            partner_section.save(update_fields=["is_active", "updated_at"])

        trust_section = self._get_or_create_section(page, "trust_signals", sort_order=9)
        trust_section.is_active = True
        trust_section.eyebrow = "Why teams trust Zreta"
        trust_section.title = "Built for real operations"
        trust_section.subtitle = "Payments, security, and support you can verify on this site."
        trust_section.save()

        Testimonial.objects.filter(
            author_name__in=["Sarah Okonkwo", "Rev. James Mwangi", "Dr. Amina Hassan"]
        ).update(is_published=False, show_on_home=False)

        NewsArticle.objects.filter(slug="enterprise-platform-expands-18-countries").update(is_published=False)

        if options["products"]:
            self._sync_product_featured_flags()

        self.stdout.write(self.style.SUCCESS("Homepage CMS content synced."))

    def _sync_product_featured_flags(self):
        for product in Product.objects.all():
            featured = product.slug == "churchhub" and product.status == ProductStatus.GA
            if product.is_featured != featured:
                product.is_featured = featured
                product.save(update_fields=["is_featured", "updated_at"])
        self.stdout.write("Product featured flags normalized (ChurchHub-first).")

    def _get_or_create_section(self, page, key, sort_order):
        section, _ = PageSection.objects.get_or_create(
            page=page,
            section_key=key,
            defaults={"sort_order": sort_order, "is_active": True},
        )
        return section

    def _sync_header(self, page, key, title, subtitle, eyebrow=""):
        section = PageSection.objects.filter(page=page, section_key=key).first()
        if not section:
            return
        section.eyebrow = eyebrow
        section.title = title
        section.subtitle = subtitle
        section.is_active = True
        section.save()

    def _sync_section(self, page, key, items, item_factory):
        section = PageSection.objects.filter(page=page, section_key=key).first()
        if not section:
            section = PageSection.objects.create(page=page, section_key=key, is_active=True, sort_order=0)
        section.items.all().delete()
        for i, item in enumerate(items):
            item_factory(section, item, i)

    def _why_item(self, section, item, index):
        SectionItem.objects.create(
            section=section,
            title=item["title"],
            description=item["description"],
            icon=item["icon"],
            sort_order=index,
            is_active=True,
        )

    def _industry_item(self, section, item, index):
        SectionItem.objects.create(
            section=section,
            title=item["name"],
            description=item["description"],
            icon=item["icon"],
            extra_data={"products": item["products"]},
            sort_order=index,
            is_active=True,
        )

    def _stat_item(self, section, item, index):
        SectionItem.objects.create(
            section=section,
            title=item["label"],
            value=item["value"],
            sort_order=index,
            is_active=True,
        )

    def _trust_item(self, section, item, index):
        SectionItem.objects.create(
            section=section,
            title=item["title"],
            description=item["description"],
            icon=item["icon"],
            sort_order=index,
            is_active=True,
        )
