"""
Sync homepage CMS content to the current honest marketing baseline.

Usage:
    python manage.py sync_homepage
    python manage.py sync_homepage --products
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from cms.models import CMSPage, HeroBanner, NewsArticle, PageSection, PageType, SectionItem, Testimonial
from products.models import Product, ProductStatus
from website.content import (
    CTA,
    HERO,
    INDUSTRIES,
    NEWSLETTER,
    REQUEST_DEMO,
    START_TRIAL,
    STATISTICS,
    TRUST_SIGNALS,
    WHY_CHOOSE_US,
)


class Command(BaseCommand):
    help = "Refresh homepage hero, sections, stats, trust signals, and platform branding from the canonical baseline."

    def add_arguments(self, parser):
        parser.add_argument(
            "--products",
            action="store_true",
            help="Also normalize homepage featured flags for all GA/BETA products.",
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
            hero.cta_primary_label = HERO.get("cta_primary_label", "Explore products")
            hero.cta_primary_url = HERO.get("cta_primary_url", "")
            hero.cta_secondary_label = HERO.get("cta_secondary_label", "Request a demo")
            hero.cta_secondary_url = HERO.get("cta_secondary_url", "#request-demo")
            hero.is_active = True
            hero.save()

        page.meta_title = "Zreta — Modular enterprise software"
        page.meta_description = (
            "Zreta markets and bills modular products including ChurchHub and CoreTrust — "
            "with GHS pricing, Mobile Money, shared portal access, and enterprise security."
        )
        page.save(update_fields=["meta_title", "meta_description", "updated_at"])

        self._sync_section(page, "why_choose_us", WHY_CHOOSE_US, item_factory=self._why_item)
        self._sync_section(page, "industries", INDUSTRIES, item_factory=self._industry_item)
        self._sync_section(page, "statistics", STATISTICS, item_factory=self._stat_item)
        self._sync_section(page, "trust_signals", TRUST_SIGNALS, item_factory=self._trust_item)

        self._sync_header(page, "featured_products", "Live products on Zreta", "ChurchHub and CoreTrust are live today — each with shared billing, security, and customer portal access.", eyebrow="Products")
        self._sync_header(page, "statistics", "Built for serious operations", "Shared standards across every Zreta product.", eyebrow="Platform")
        self._sync_header(page, "cta", CTA["title"], CTA["subtitle"])
        self._ensure_header(
            page,
            "start_trial",
            START_TRIAL["title"],
            START_TRIAL["subtitle"],
            eyebrow=START_TRIAL["eyebrow"],
            sort_order=7,
        )
        self._ensure_header(
            page,
            "request_demo",
            REQUEST_DEMO["title"],
            REQUEST_DEMO["subtitle"],
            eyebrow=REQUEST_DEMO["eyebrow"],
            sort_order=8,
        )
        self._sync_header(page, "newsletter", NEWSLETTER["title"], NEWSLETTER["subtitle"])

        trial_section = self._get_or_create_section(page, "start_trial", sort_order=7)
        trial_section.items.all().delete()
        for i, (title, icon) in enumerate(
            [
                ("Live product experience — not a sandbox brochure", "check"),
                ("Account created on the product site", "check"),
                ("Return to your Zreta portal anytime for billing", "check"),
            ]
        ):
            SectionItem.objects.create(section=trial_section, title=title, icon=icon, sort_order=i, is_active=True)

        demo_section = self._get_or_create_section(page, "request_demo", sort_order=8)
        demo_section.items.all().delete()
        for i, (title, icon) in enumerate(
            [
                ("Demo handled by the live product team", "check-circle"),
                ("ChurchHub and CoreTrust already deployed", "check-circle"),
                ("Continue on the product landing page", "check-circle"),
                ("Sales help if you are unsure which product", "check-circle"),
            ]
        ):
            SectionItem.objects.create(section=demo_section, title=title, icon=icon, sort_order=i, is_active=True)

        partner_section = PageSection.objects.filter(page=page, section_key="partner_logos").first()
        if partner_section:
            partner_section.is_active = False
            partner_section.save(update_fields=["is_active", "updated_at"])

        trust_section = self._get_or_create_section(page, "trust_signals", sort_order=9)
        trust_section.is_active = True
        trust_section.eyebrow = "Evidence"
        trust_section.title = "What you can verify"
        trust_section.subtitle = "Open these pages — each item points to something published on this site."
        trust_section.save()

        why_section = PageSection.objects.filter(page=page, section_key="why_choose_us").first()
        if why_section:
            why_section.eyebrow = "Platform"
            why_section.title = "Shared layer behind live products"
            why_section.subtitle = "Security, billing, and operations practices you can open — including what we mean by reliability."
            why_section.is_active = True
            why_section.save()

        how_section = PageSection.objects.filter(page=page, section_key="how_it_works").first()
        if how_section:
            how_section.is_active = False
            how_section.save(update_fields=["is_active", "updated_at"])

        cta_section = PageSection.objects.filter(page=page, section_key="cta").first()
        if cta_section:
            cta_section.is_active = False
            cta_section.save(update_fields=["is_active", "updated_at"])

        Testimonial.objects.filter(
            author_name__in=["Sarah Okonkwo", "Rev. James Mwangi", "Dr. Amina Hassan"]
        ).update(is_published=False, show_on_home=False)

        NewsArticle.objects.filter(slug="enterprise-platform-expands-18-countries").update(is_published=False)

        try:
            from marketing.models import BlogPost, CaseStudy, SuccessStory

            BlogPost.objects.filter(
                slug__in=[
                    "enterprise-platform-achieves-soc-2-type-ii",
                    "enterprise-platform-expands-18-countries",
                ]
            ).update(is_published=False, is_featured=False)

            # Seeded fictional proof must not appear as customer evidence.
            SuccessStory.objects.filter(
                slug__in=["unity-microfinance-success"]
            ).update(is_published=False, is_featured=False)
            SuccessStory.objects.filter(company__icontains="Unity").update(
                is_published=False, is_featured=False
            )
            CaseStudy.objects.filter(
                slug__in=["horizon-academy-case-study"]
            ).update(is_published=False, is_featured=False)
            CaseStudy.objects.filter(client_name__icontains="Horizon").update(
                is_published=False, is_featured=False
            )
        except Exception:
            pass

        self._rewrite_hospital_roadmap_content()
        self._scrub_unsupported_trust_claims()
        self._fix_copy_typos()
        self._sync_platform_branding()
        self._sync_about_page()
        self._sync_roadmap_catalog()

        if options["products"]:
            self._sync_product_featured_flags()

        self.stdout.write(self.style.SUCCESS("Homepage CMS content synced."))

    def _rewrite_hospital_roadmap_content(self):
        """Keep Hospital Management messaging as roadmap — never as a live 2.0 release."""
        title = "Inside Zreta's Hospital Management Roadmap"
        excerpt = (
            "What Hospital Management is planned to cover on Zreta — "
            "not a live product release announcement."
        )
        body = (
            "Hospital Management is on the Zreta roadmap.\n\n"
            "We are exploring appointments, billing, and clinical workflows for clinics "
            "and hospitals. This article is a roadmap note, not a generally-available release.\n\n"
            "ChurchHub and CoreTrust are the live products on Zreta today. Hospital Management "
            "remains Coming soon until we publish it as live."
        )

        NewsArticle.objects.filter(
            Q(title__icontains="Hospital Management 2.0")
            | Q(slug="introducing-hospital-management-2-0")
        ).update(
            title=title,
            excerpt=excerpt,
            body=body,
            is_published=False,
        )

        try:
            from django.utils import timezone
            from marketing.models import BlogPost

            target_slug = "inside-zretas-hospital-management-roadmap"
            posts = list(
                BlogPost.objects.filter(
                    Q(title__icontains="Hospital Management 2.0")
                    | Q(slug="introducing-hospital-management-2-0")
                    | Q(title__icontains="Hospital Management: what we're building")
                    | Q(slug=target_slug)
                )
            )
            primary = None
            for post in posts:
                if post.slug == target_slug or "2.0" in (post.title or ""):
                    primary = post
                    break
            if primary is None and posts:
                primary = posts[0]
            if primary is not None:
                primary.title = title
                primary.slug = target_slug
                primary.excerpt = excerpt
                primary.body = body
                primary.meta_title = title
                primary.meta_description = excerpt
                primary.is_featured = False
                primary.is_published = True
                if not primary.published_at:
                    primary.published_at = timezone.now()
                primary.save()
                for post in posts:
                    if post.pk != primary.pk:
                        post.is_published = False
                        post.is_featured = False
                        post.save(update_fields=["is_published", "is_featured", "updated_at"])
        except Exception:
            pass

    def _scrub_unsupported_trust_claims(self):
        """Rewrite leftover CMS slogans and trial contradictions that outrun public proof."""
        replacements = {
            "The platform global organizations trust.": (
                "Enterprise software for organizations that scale."
            ),
            "The platform global organizations trust": (
                "Enterprise software for organizations that scale"
            ),
            "global organizations trust": "organizations that scale",
            "Trusted by industry leaders": "Built for serious operations",
            "organizations trust worldwide": "organizations that scale",
            "Why teams trust Zreta": "What you can verify",
            "Built for enterprise reliability": "Shared layer behind live products",
            # Trial duration — portal default is 30 days; never advertise 14-day trials.
            "14-day free trial": "30-day free trial",
            "14-day trial": "30-day trial",
            "14 day free trial": "30-day free trial",
            "14 day trial": "30-day trial",
            "14 days — Free trial": "30 days — ChurchHub free trial",
            "14 days": "30 days",  # applied carefully via field filters below for trial contexts
            "Start a 14-day trial": "Start a 30-day trial",
            "activate a 30-day trial": "start on the live product (ChurchHub trial or CoreTrust demo)",
            "Free trial on every plan": "ChurchHub: 30-day trial · CoreTrust: request a demo",
            "free trial on every plan": "ChurchHub: 30-day trial · CoreTrust: request a demo",
            "Every product offers a free trial with full feature access.": (
                "ChurchHub offers a 30-day free trial. CoreTrust starts with a product demo."
            ),
            "every product offers a free trial": (
                "ChurchHub offers a 30-day free trial; CoreTrust starts with a demo"
            ),
            "Create an account and activate a 30-day trial": (
                "Continue to ChurchHub for a 30-day trial, or request a CoreTrust demo"
            ),
            (
                "Our platform includes ChurchHub, CoreTrust, ERP Suite, School Management, "
                "Hospital Management, and HR & Payroll — each deployable independently or together."
            ): (
                "Zreta markets and bills ChurchHub and CoreTrust today. Additional industry "
                "products appear in the catalog as roadmap items."
            ),
            "each deployable independently or together": (
                "with live products today and roadmap items labelled honestly"
            ),
            "30-day demo via its product site": "30-day free trial via its product site",
        }
        # Exact 14-days replacements only in trial-related copy (not refund policy pages).
        trial_only_replacements = {
            "14 days": "30 days",
            "14-day": "30-day",
        }

        def apply_replacements(value: str, *, trial_context: bool = False) -> str:
            new_value = value
            for old, new in replacements.items():
                if old == "14 days":
                    continue
                if old in new_value:
                    new_value = new_value.replace(old, new)
            if trial_context:
                lower = new_value.lower()
                if "trial" in lower or "free" in lower or "plan" in lower:
                    for old, new in trial_only_replacements.items():
                        if old in new_value and "refund" not in lower:
                            new_value = new_value.replace(old, new)
            return new_value

        for banner in HeroBanner.objects.all():
            changed = False
            for field in ("eyebrow", "headline", "subheadline", "trust_text"):
                value = getattr(banner, field) or ""
                new_value = apply_replacements(value, trial_context=True)
                if new_value != value:
                    setattr(banner, field, new_value)
                    changed = True
            if changed:
                banner.save()

        for section in PageSection.objects.all():
            changed = False
            for field in ("eyebrow", "title", "subtitle", "body"):
                value = getattr(section, field) or ""
                new_value = apply_replacements(value, trial_context=True)
                if new_value != value:
                    setattr(section, field, new_value)
                    changed = True
            if changed:
                section.save()

        for item in SectionItem.objects.all():
            changed = False
            for field in ("title", "description", "value"):
                if not hasattr(item, field):
                    continue
                value = getattr(item, field) or ""
                if not isinstance(value, str):
                    continue
                new_value = apply_replacements(value, trial_context=True)
                if new_value != value:
                    setattr(item, field, new_value)
                    changed = True
            if changed:
                item.save()

        # FAQs often retain old trial copy.
        try:
            from cms.models import FAQ

            for faq in FAQ.objects.all():
                changed = False
                for field in ("question", "answer"):
                    value = getattr(faq, field) or ""
                    new_value = apply_replacements(value, trial_context=True)
                    if new_value != value:
                        setattr(faq, field, new_value)
                        changed = True
                if changed:
                    faq.save()
        except Exception:
            pass

    def _fix_copy_typos(self):
        from products.models import Product

        typo_pairs = (
            ("system..", "system."),
            ("system.s", "system."),  # legacy mistype from earlier scrubbers
        )

        for product in Product.objects.all():
            changed_fields = []
            for field in ("short_description", "long_description", "tagline"):
                value = getattr(product, field) or ""
                new_value = value
                for old, new in typo_pairs:
                    if old in new_value:
                        new_value = new_value.replace(old, new)
                if new_value != value:
                    setattr(product, field, new_value)
                    changed_fields.append(field)
            if changed_fields:
                product.save(update_fields=[*changed_fields, "updated_at"])

        for section in PageSection.objects.all():
            body = section.body or ""
            new_body = body
            for old, new in typo_pairs:
                if old in new_body:
                    new_body = new_body.replace(old, new)
            if new_body != body:
                section.body = new_body
                section.save(update_fields=["body", "updated_at"])

    def _sync_roadmap_catalog(self):
        """Ensure roadmap catalog entries stay published as Coming soon (no broken nav links)."""
        roadmap_slugs = (
            "erp-suite",
            "school-management",
            "hospital-management",
            "hr-payroll",
        )
        updated = Product.objects.filter(slug__in=roadmap_slugs).update(
            status=ProductStatus.COMING_SOON,
            is_featured=False,
            is_published=True,
        )
        # Soften present-tense Hospital copy that reads as if GA were live.
        hospital = Product.objects.filter(slug="hospital-management").first()
        if hospital:
            hospital.short_description = (
                "Roadmap product for appointments, billing, pharmacy, lab, and patient records."
            )
            hospital.long_description = (
                "Hospital Management is on the Zreta roadmap. Planned capabilities include "
                "clinical and administrative workflows for hospitals and clinics — EMR-lite, "
                "billing, pharmacy, and lab integrations — when the product reaches GA."
            )
            hospital.tagline = "Healthcare operations — on the roadmap"
            hospital.save(
                update_fields=[
                    "short_description",
                    "long_description",
                    "tagline",
                    "updated_at",
                ]
            )
        if updated:
            self.stdout.write(f"Roadmap catalog entries normalized: {updated}")

    def _sync_about_page(self):
        about = CMSPage.objects.filter(page_type=PageType.ABOUT).first()
        if not about:
            return
        hero = about.hero
        if hero:
            hero.eyebrow = "Company"
            hero.headline = "About Zreta"
            hero.subheadline = (
                "Zreta markets and bills modular enterprise products. "
                "ChurchHub and CoreTrust are live applications; more industries are on the roadmap."
            )
            hero.save()
        from cms.models import TeamMember

        TeamMember.objects.filter(
            full_name__in=["Sarah Okonkwo", "James Mwangi", "Dr. Amina Hassan", "David Chen"]
        ).update(is_published=False, show_on_about=False)

    def _sync_platform_branding(self):
        from control_room.models import PlatformSettings

        settings_obj = PlatformSettings.load()
        updated = []
        if settings_obj.site_name in ("Enterprise Platform", ""):
            settings_obj.site_name = "Zreta"
            updated.append("site_name")
        if "Enterprise Platform" in (settings_obj.footer_copyright or ""):
            settings_obj.footer_copyright = "© Zreta. All rights reserved."
            updated.append("footer_copyright")
        if settings_obj.default_seo_title in ("Enterprise Platform", ""):
            settings_obj.default_seo_title = "Zreta"
            updated.append("default_seo_title")
        if settings_obj.site_tagline in ("Classic software for modern enterprise teams", ""):
            settings_obj.site_tagline = "Modular enterprise software for growing organizations"
            updated.append("site_tagline")
        if updated:
            settings_obj.save(update_fields=[*updated, "updated_at"])
            self.stdout.write(f"Platform settings updated: {', '.join(updated)}")

    def _sync_product_featured_flags(self):
        live_slugs = {"churchhub", "microfinance-core"}
        for product in Product.objects.filter(is_published=True):
            featured = (
                product.slug in live_slugs
                and product.status in (ProductStatus.GA, ProductStatus.BETA)
            )
            if product.is_featured != featured:
                product.is_featured = featured
                product.save(update_fields=["is_featured", "updated_at"])
        self.stdout.write("Product featured flags limited to live ChurchHub and CoreTrust.")

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

    def _ensure_header(self, page, key, title, subtitle, eyebrow="", sort_order=0):
        section = self._get_or_create_section(page, key, sort_order=sort_order)
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
        extra = {}
        if item.get("url_name"):
            extra["url_name"] = item["url_name"]
        SectionItem.objects.create(
            section=section,
            title=item["title"],
            description=item["description"],
            icon=item["icon"],
            extra_data=extra,
            sort_order=index,
            is_active=True,
        )


    def _industry_item(self, section, item, index):
        extra = {"products": item["products"]}
        if item.get("url_name"):
            extra["url_name"] = item["url_name"]
        SectionItem.objects.create(
            section=section,
            title=item["name"],
            description=item["description"],
            icon=item["icon"],
            extra_data=extra,
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
        extra = {}
        if item.get("url_name"):
            extra["url_name"] = item["url_name"]
        SectionItem.objects.create(
            section=section,
            title=item["title"],
            description=item["description"],
            icon=item["icon"],
            extra_data=extra,
            sort_order=index,
            is_active=True,
        )
