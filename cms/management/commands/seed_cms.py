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
    NewsArticle,
    PageSection,
    PageType,
    SectionItem,
    TeamMember,
    Testimonial,
)
from website.content import (
    HERO,
    INDUSTRIES,
    PARTNER_LOGOS,
    STATISTICS,
    TESTIMONIALS,
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
            cta_primary_label="Start Free Trial",
            cta_secondary_label="Request a Demo",
            cta_secondary_url="#request-demo",
            is_active=True,
        )

        home_page = CMSPage.objects.create(
            title="Home",
            slug="home",
            page_type=PageType.HOME,
            hero=hero,
            is_published=True,
            published_at=now,
            meta_title="Enterprise Software for Every Industry",
        )

        section_defs = [
            ("featured_products", "Our Products", "Featured products", "Modular SaaS solutions designed for your industry."),
            ("why_choose_us", "Why Choose Us", "Built for enterprise reliability", "The platform global organizations trust."),
            ("industries", "Industries", "Solutions for every sector", "Purpose-built products for your industry."),
            ("testimonials", "Testimonials", "What our customers say", "Organizations worldwide rely on our platform."),
            ("latest_news", "Latest News", "From our blog", "Product updates, guides, and company news."),
            ("statistics", "", "", ""),
            ("cta", "", "Ready to transform your organization?", "Join 2,500+ organizations on our platform."),
            ("partner_logos", "Partners", "Trusted by industry leaders", "Technology and implementation partners worldwide."),
            ("request_demo", "Request a Demo", "See the platform in action", "Schedule a personalized walkthrough."),
            ("newsletter", "", "Stay ahead with product insights", "Monthly updates on features and best practices."),
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
            SectionItem.objects.create(
                section=sections["why_choose_us"],
                title=item["title"],
                description=item["description"],
                icon=item["icon"],
                sort_order=i,
            )

        for i, item in enumerate(INDUSTRIES):
            SectionItem.objects.create(
                section=sections["industries"],
                title=item["name"],
                description=item["description"],
                icon=item["icon"],
                extra_data={"products": item["products"]},
                sort_order=i,
            )

        for i, item in enumerate(STATISTICS):
            SectionItem.objects.create(
                section=sections["statistics"],
                title=item["label"],
                value=item["value"],
                sort_order=i,
            )

        for i, item in enumerate(PARTNER_LOGOS):
            SectionItem.objects.create(
                section=sections["partner_logos"],
                title=item["name"],
                sort_order=i,
            )

        demo_benefits = [
            ("30-minute tailored demo", "check-circle"),
            ("Q&A with product experts", "check-circle"),
            ("Custom pricing proposal", "check-circle"),
            ("No commitment required", "check-circle"),
        ]
        for i, (title, icon) in enumerate(demo_benefits):
            SectionItem.objects.create(
                section=sections["request_demo"],
                title=title,
                icon=icon,
                sort_order=i,
            )

        for i, item in enumerate(TESTIMONIALS):
            Testimonial.objects.create(
                quote=item["quote"],
                author_name=item["name"],
                author_role=item["role"],
                company=item["company"],
                initials=item["initials"],
                show_on_home=True,
                is_published=True,
                sort_order=i,
            )

        NewsArticle.objects.create(
            title="Enterprise Platform expands to 18 countries",
            slug="enterprise-platform-expands-18-countries",
            category="Company News",
            excerpt="Our global footprint continues to grow with new regional data centers and local support teams.",
            body="Enterprise Platform expands operations across Africa, Europe, and Asia-Pacific.",
            is_featured=True,
            is_published=True,
            published_at=now,
        )

        about_hero = HeroBanner.objects.create(
            name="About Hero",
            placement=HeroPlacement.ABOUT,
            eyebrow="About Us",
            headline="Building software that powers organizations worldwide",
            subheadline="We deliver modular, enterprise-grade SaaS for industries that demand reliability, security, and scale.",
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
            ("mission", "Our Mission", "Empower every organization with software built for their world.", ""),
            ("vision", "Our Vision", "A unified platform where modular products share identity, data, and trust.", ""),
            ("values", "Our Values", "", ""),
            ("team", "Our Team", "Leadership & experts", "The people building the platform organizations trust."),
        ]
        about_section_objs = {}
        for i, (key, eyebrow, title, subtitle) in enumerate(about_sections):
            body = ""
            if key == "mission":
                body = "We build enterprise SaaS that helps churches, hospitals, schools, and financial institutions run smarter operations."
            elif key == "vision":
                body = "Organizations should not choose between best-of-breed tools and unified platforms — they deserve both."
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
            ("Customer obsession", "We succeed when our customers succeed.", "heart"),
            ("Security first", "Trust is earned through rigorous security and compliance.", "shield-check"),
            ("Modular excellence", "Each product stands alone and integrates seamlessly.", "layers"),
        ]
        for i, (title, desc, icon) in enumerate(values):
            SectionItem.objects.create(
                section=about_section_objs["values"],
                title=title,
                description=desc,
                icon=icon,
                sort_order=i,
            )

        team = [
            ("Sarah Okonkwo", "Chief Executive Officer", "Executive", True),
            ("James Mwangi", "Chief Technology Officer", "Engineering", True),
            ("Dr. Amina Hassan", "Chief Product Officer", "Product", True),
            ("David Chen", "VP Customer Success", "Customer Success", False),
        ]
        for i, (name, role, dept, leadership) in enumerate(team):
            TeamMember.objects.create(
                full_name=name,
                role=role,
                department=dept,
                bio=f"{name} leads our {dept.lower()} organization with deep industry expertise.",
                is_leadership=leadership,
                show_on_about=True,
                is_published=True,
                sort_order=i,
            )

        faq_cat = FAQCategory.objects.create(name="General", slug="general", sort_order=0)
        faqs = [
            ("What products are included in the platform?", "Our platform includes ChurchHub, Microfinance Core, ERP Suite, School Management, Hospital Management, and HR & Payroll — each deployable independently or together."),
            ("Is there a free trial?", "Yes. Every product offers a free trial with full feature access. No credit card required."),
            ("Do you offer on-premise deployment?", "We primarily offer cloud SaaS with dedicated tenant options. Contact sales for hybrid or private cloud arrangements."),
            ("What support SLAs do you provide?", "Standard plans include business-hours support. Enterprise plans include 24/7 priority support with guaranteed response times."),
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
