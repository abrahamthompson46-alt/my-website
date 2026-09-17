"""
Seed CMS content from the original static homepage data.
Usage: python manage.py seed_cms
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from cms.models import (
    CMSPage,
    FAQ,
    FAQCategory,
    HeroBanner,
    HeroPlacement,
    PageSection,
    PageType,
    SectionItem,
)
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
    help = "Seed CMS pages, hero banners, testimonials, news, FAQs, and team members."

    @transaction.atomic
    def handle(self, *args, **options):
        if CMSPage.objects.filter(page_type=PageType.HOME).exists():
            self.stdout.write(self.style.WARNING("CMS content already exists. Skipping seed."))
            return

        now = timezone.now()

        hero = HeroBanner.objects.create(
            name="Home Hero",
            placement=HeroPlacement.HOME,
            eyebrow=HERO["eyebrow"],
            headline=HERO["headline"],
            subheadline=HERO["subheadline"],
            trust_text=HERO["trust_text"],
            cta_primary_label=HERO.get("cta_primary_label", "Explore products"),
            cta_primary_url=HERO.get("cta_primary_url", ""),
            cta_secondary_label=HERO.get("cta_secondary_label", "Request a demo"),
            cta_secondary_url=HERO.get("cta_secondary_url", "#request-demo"),
            is_active=True,
        )

        home_page = CMSPage.objects.create(
            title="Home",
            slug="home",
            page_type=PageType.HOME,
            hero=hero,
            is_published=True,
            published_at=now,
            meta_title="Zreta — Modular enterprise software",
            meta_description=(
                "Zreta is a modular enterprise software platform. Products for faith communities, "
                "financial services, education, healthcare, ERP, and HR — with GHS pricing, "
                "Mobile Money, and enterprise security."
            ),
        )

        section_defs = [
            ("featured_products", "Products", "Live products on Zreta", "ChurchHub and CoreTrust are live today — each with shared billing, security, and customer portal access."),
            ("why_choose_us", "Platform", "Shared layer behind live products", "Security, billing, and operations practices you can open — including what we mean by reliability."),
            ("industries", "Industries", "Solutions by sector", "Outcome-led pages for churches, microfinance, education, and healthcare."),
            ("testimonials", "Testimonials", "What our customers say", "Verified customer stories appear here as they are published."),
            ("latest_news", "Latest News", "From our blog", "Product updates, guides, and company news."),
            ("statistics", "Platform", "Built for serious operations", "Shared standards across every Zreta product."),
            ("cta", "", CTA["title"], CTA["subtitle"]),
            ("trust_signals", "Evidence", "What you can verify", "Open these pages — each item points to something published on this site."),
            ("start_trial", START_TRIAL["eyebrow"], START_TRIAL["title"], START_TRIAL["subtitle"]),
            ("request_demo", REQUEST_DEMO["eyebrow"], REQUEST_DEMO["title"], REQUEST_DEMO["subtitle"]),
            ("newsletter", "", NEWSLETTER["title"], NEWSLETTER["subtitle"]),
        ]

        sections = {}
        for i, (key, eyebrow, title, subtitle) in enumerate(section_defs):
            sections[key] = PageSection.objects.create(
                page=home_page,
                section_key=key,
                eyebrow=eyebrow,
                title=title,
                subtitle=subtitle,
                sort_order=i,
                is_active=True,
            )

        for i, item in enumerate(WHY_CHOOSE_US):
            extra = {}
            if item.get("url_name"):
                extra["url_name"] = item["url_name"]
            SectionItem.objects.create(
                section=sections["why_choose_us"],
                title=item["title"],
                description=item["description"],
                icon=item["icon"],
                extra_data=extra,
                sort_order=i,
            )

        for i, item in enumerate(INDUSTRIES):
            extra = {"products": item["products"]}
            if item.get("url_name"):
                extra["url_name"] = item["url_name"]
            SectionItem.objects.create(
                section=sections["industries"],
                title=item["name"],
                description=item["description"],
                icon=item["icon"],
                extra_data=extra,
                sort_order=i,
            )

        for i, item in enumerate(STATISTICS):
            SectionItem.objects.create(
                section=sections["statistics"],
                title=item["label"],
                value=item["value"],
                sort_order=i,
            )

        for i, item in enumerate(TRUST_SIGNALS):
            extra = {}
            if item.get("url_name"):
                extra["url_name"] = item["url_name"]
            SectionItem.objects.create(
                section=sections["trust_signals"],
                title=item["title"],
                description=item["description"],
                icon=item["icon"],
                extra_data=extra,
                sort_order=i,
            )

        trial_benefits = [
            ("Live product experience — not a sandbox brochure", "check"),
            ("Account created on the product site", "check"),
            ("Return to your Zreta portal anytime for billing", "check"),
        ]
        for i, (title, icon) in enumerate(trial_benefits):
            SectionItem.objects.create(
                section=sections["start_trial"],
                title=title,
                icon=icon,
                sort_order=i,
            )

        demo_benefits = [
            ("Demo handled by the live product team", "check-circle"),
            ("ChurchHub and CoreTrust already deployed", "check-circle"),
            ("Continue on the product landing page", "check-circle"),
            ("Sales help if you are unsure which product", "check-circle"),
        ]
        for i, (title, icon) in enumerate(demo_benefits):
            SectionItem.objects.create(
                section=sections["request_demo"],
                title=title,
                icon=icon,
                sort_order=i,
            )

        about_hero = HeroBanner.objects.create(
            name="About Hero",
            placement=HeroPlacement.ABOUT,
            eyebrow="Company",
            headline="About Zreta",
            subheadline=(
                "Zreta markets and bills modular enterprise products. "
                "ChurchHub and CoreTrust are live applications; more industries are on the roadmap."
            ),
            is_active=True,
        )

        about_page = CMSPage.objects.create(
            title="About",
            slug="about",
            page_type=PageType.ABOUT,
            hero=about_hero,
            is_published=True,
            published_at=now,
        )

        about_sections = [
            ("mission", "Mission", "Help organizations run with modular software they can trust.", ""),
            ("vision", "How we work", "Storefront plus live product applications — not one monolith claiming every engine.", ""),
            ("values", "What we publish", "", ""),
        ]
        about_section_objs = {}
        for i, (key, eyebrow, title, subtitle) in enumerate(about_sections):
            body = ""
            if key == "mission":
                body = (
                    "We sell and support modular products for churches and microfinance institutions today, "
                    "with shared billing, portal access, and security practices on Zreta."
                )
            elif key == "vision":
                body = (
                    "ChurchHub and CoreTrust run as external applications. Zreta.com is the marketing, "
                    "billing, and customer-portal layer. Roadmap products are labelled honestly until GA."
                )
            about_section_objs[key] = PageSection.objects.create(
                page=about_page,
                section_key=key,
                eyebrow=eyebrow,
                title=title,
                subtitle=subtitle,
                body=body,
                sort_order=i,
            )

        values = [
            ("Evidence over slogans", "We publish Live vs Roadmap labels and avoid unverified customer counts.", "check-circle"),
            ("Security first", "Staff MFA, audit logs, private payment proofs, and a public Security Center.", "shield-check"),
            ("Modular products", "Each live product stands alone and connects through Zreta billing and portal.", "layers"),
        ]
        for i, (title, desc, icon) in enumerate(values):
            SectionItem.objects.create(
                section=about_section_objs["values"],
                title=title,
                description=desc,
                icon=icon,
                sort_order=i,
            )

        faq_cat = FAQCategory.objects.create(name="General", slug="general", sort_order=0)
        faqs = [
            ("What products are included in the platform?", "Zreta markets and bills ChurchHub and CoreTrust today. Additional industry products appear in the catalog as roadmap items."),
            ("Is there a free trial?", "ChurchHub offers a 30-day demo via its product site. CoreTrust onboarding is handled with the product team. Roadmap products are not trialable yet."),
            ("Do you offer on-premise deployment?", "We primarily offer cloud SaaS with dedicated tenant options. Contact sales for hybrid or private cloud arrangements."),
            ("What support SLAs do you provide?", "Published support targets are listed on this site. Contact us for plan-specific response commitments."),
        ]
        for i, (question, answer) in enumerate(faqs):
            FAQ.objects.create(
                category=faq_cat,
                question=question,
                answer=answer,
                sort_order=i,
                is_published=True,
            )

        self.stdout.write(self.style.SUCCESS("CMS content seeded successfully."))
