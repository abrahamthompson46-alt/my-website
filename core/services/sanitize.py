"""Platform sanitization: report and repair DB/UI consistency issues."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from typing import Callable

from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone

from common.services.trial_provisioning import expire_due_trials
from customer_portal.models import Invoice, License, Subscription
from customer_portal.models.invoice import InvoiceStatus
from customer_portal.models.license import LicenseStatus
from customer_portal.models.subscription import SubscriptionStatus
from organizations.services import ensure_default_organization
from payments.models import Payment, PaymentStatus
from products.models import Product, ProductStatus
from products.services.availability import PURCHASABLE_STATUSES


CORETRUST_SLUG = "microfinance-core"
CORETRUST_NAME = "CoreTrust"
LEGACY_NAME = "Microfinance Core"


@dataclass
class Finding:
    code: str
    severity: str  # info | warning | error
    message: str
    count: int = 0
    sample_ids: list[str] = field(default_factory=list)
    fixed: int = 0


@dataclass
class SanitizeReport:
    findings: list[Finding] = field(default_factory=list)
    fixed_total: int = 0

    def add(self, finding: Finding) -> None:
        self.findings.append(finding)
        self.fixed_total += finding.fixed


def _sample_ids(queryset, limit: int = 8) -> list[str]:
    return [str(pk) for pk in queryset.values_list("pk", flat=True)[:limit]]


def _resolve_org_for_user(user):
    if user is None:
        return None
    return ensure_default_organization(user)


def check_null_organizations(*, fix: bool = False) -> Finding:
    """Backfill organization on billing rows that lost tenant context."""
    models = (
        ("subscription", Subscription.objects.filter(organization__isnull=True)),
        ("license", License.objects.filter(organization__isnull=True)),
        ("invoice", Invoice.objects.filter(organization__isnull=True)),
        ("payment", Payment.objects.filter(organization__isnull=True)),
    )
    total = 0
    fixed = 0
    samples: list[str] = []

    for label, qs in models:
        count = qs.count()
        total += count
        samples.extend(f"{label}:{pk}" for pk in qs.values_list("pk", flat=True)[:3])
        if not fix or count == 0:
            continue
        if label == "payment":
            related = ["user", "invoice"]
        elif label == "license":
            related = ["user", "subscription"]
        else:
            related = ["user"]
        for obj in qs.select_related(*related):
            org = getattr(obj, "organization", None)
            if org is None and getattr(obj, "subscription_id", None):
                org = getattr(obj.subscription, "organization", None)
            if org is None and getattr(obj, "invoice_id", None):
                org = getattr(obj.invoice, "organization", None)
            if org is None:
                org = _resolve_org_for_user(getattr(obj, "user", None))
            if org is None:
                continue
            obj.organization = org
            obj.save(update_fields=["organization", "updated_at"])
            fixed += 1

    return Finding(
        code="null_organization",
        severity="error" if total else "info",
        message=(
            f"{total} billing row(s) missing organization"
            + (f"; backfilled {fixed}" if fix else "")
        ),
        count=total,
        sample_ids=samples[:8],
        fixed=fixed,
    )


def check_license_org_alignment(*, fix: bool = False) -> Finding:
    """Licenses whose organization differs from their subscription organization."""
    qs = (
        License.objects.filter(subscription__isnull=False)
        .exclude(organization_id=F("subscription__organization_id"))
        .exclude(subscription__organization__isnull=True)
    )
    count = qs.count()
    fixed = 0
    if fix and count:
        for license_obj in qs.select_related("subscription"):
            license_obj.organization_id = license_obj.subscription.organization_id
            license_obj.save(update_fields=["organization", "updated_at"])
            fixed += 1

    return Finding(
        code="license_org_mismatch",
        severity="warning" if count else "info",
        message=(
            f"{count} license(s) with organization != subscription.organization"
            + (f"; aligned {fixed}" if fix else "")
        ),
        count=count,
        sample_ids=_sample_ids(qs),
        fixed=fixed,
    )


def check_cross_user_links(*, fix: bool = False) -> Finding:
    """Detect (and optionally detach) invoices/licenses linked to another user's subscription."""
    invoice_qs = Invoice.objects.filter(subscription__isnull=False).exclude(
        user_id=F("subscription__user_id")
    )
    license_qs = License.objects.filter(subscription__isnull=False).exclude(
        user_id=F("subscription__user_id")
    )
    count = invoice_qs.count() + license_qs.count()
    samples = [f"invoice:{pk}" for pk in invoice_qs.values_list("pk", flat=True)[:4]]
    samples += [f"license:{pk}" for pk in license_qs.values_list("pk", flat=True)[:4]]
    fixed = 0
    if fix and count:
        # Detach the bad link rather than rewriting ownership.
        fixed += invoice_qs.update(subscription=None)
        for license_obj in license_qs:
            license_obj.subscription = None
            license_obj.status = LicenseStatus.REVOKED
            license_obj.save(update_fields=["subscription", "status", "updated_at"])
            fixed += 1

    return Finding(
        code="cross_user_link",
        severity="error" if count else "info",
        message=(
            f"{count} invoice/license row(s) linked across different users"
            + (f"; detached/revoked {fixed}" if fix else " (use --fix to detach)")
        ),
        count=count,
        sample_ids=samples,
        fixed=fixed,
    )


def check_status_date_invariants(*, fix: bool = False) -> Finding:
    """Impossible status/date combinations; apply deterministic repairs when asked."""
    today = timezone.now().date()
    now = timezone.now()
    fixed = 0
    samples: list[str] = []

    trial_missing_end = Subscription.objects.filter(
        status=SubscriptionStatus.TRIAL, trial_ends_at__isnull=True
    )
    cancelled_missing = Subscription.objects.filter(
        status=SubscriptionStatus.CANCELLED, cancelled_at__isnull=True
    )
    paid_invoice_missing = Invoice.objects.filter(
        status=InvoiceStatus.PAID, paid_at__isnull=True
    )
    paid_payment_missing = Payment.objects.filter(
        status=PaymentStatus.SUCCEEDED, paid_at__isnull=True
    )
    active_on_expired = License.objects.filter(
        status=LicenseStatus.ACTIVE,
        subscription__status=SubscriptionStatus.EXPIRED,
    )

    buckets = [
        ("trial", trial_missing_end),
        ("cancelled", cancelled_missing),
        ("invoice", paid_invoice_missing),
        ("payment", paid_payment_missing),
        ("license", active_on_expired),
    ]
    total = sum(qs.count() for _, qs in buckets)
    for label, qs in buckets:
        samples.extend(f"{label}:{pk}" for pk in qs.values_list("pk", flat=True)[:2])

    if fix and total:
        for sub in trial_missing_end:
            sub.trial_ends_at = (sub.started_at or today) + timedelta(days=30)
            sub.save(update_fields=["trial_ends_at", "updated_at"])
            fixed += 1
        for sub in cancelled_missing:
            sub.cancelled_at = sub.updated_at.date() if sub.updated_at else today
            sub.save(update_fields=["cancelled_at", "updated_at"])
            fixed += 1
        fixed += paid_invoice_missing.update(paid_at=today)
        fixed += paid_payment_missing.update(paid_at=now)
        fixed += active_on_expired.update(status=LicenseStatus.EXPIRED)

    return Finding(
        code="status_date_invariant",
        severity="warning" if total else "info",
        message=(
            f"{total} status/date contradiction(s)"
            + (f"; repaired {fixed}" if fix else "")
        ),
        count=total,
        sample_ids=samples[:8],
        fixed=fixed,
    )


def check_featured_products(*, fix: bool = False) -> Finding:
    """Featured products should be published and purchasable (GA/Beta)."""
    bad = Product.objects.filter(is_featured=True).filter(
        Q(is_published=False) | ~Q(status__in=PURCHASABLE_STATUSES)
    )
    count = bad.count()
    fixed = 0
    if fix and count:
        fixed = bad.update(is_featured=False)
    return Finding(
        code="featured_policy",
        severity="warning" if count else "info",
        message=(
            f"{count} featured product(s) not published GA/Beta"
            + (f"; cleared featured on {fixed}" if fix else "")
        ),
        count=count,
        sample_ids=_sample_ids(bad),
        fixed=fixed,
    )


def check_coretrust_catalog(*, fix: bool = False) -> Finding:
    """Keep CoreTrust catalog row aligned with external-product model."""
    product = Product.objects.filter(slug=CORETRUST_SLUG).first()
    if product is None:
        return Finding(
            code="coretrust_missing",
            severity="warning",
            message="CoreTrust product (slug=microfinance-core) not found",
            count=1,
        )

    expected_demo = "https://micro.zreta.com/request-demo/"
    expected_register = "https://micro.zreta.com/request-demo/"
    expected_app = "https://micro.zreta.com/"

    drift = []
    if product.name != CORETRUST_NAME:
        drift.append(f"name={product.name!r}")
    if (product.external_app_url or "").rstrip("/") != expected_app.rstrip("/"):
        drift.append("external_app_url")
    if (product.demo_url or "").rstrip("/") != expected_demo.rstrip("/"):
        drift.append("demo_url")
    if (product.register_url or "").rstrip("/") != expected_register.rstrip("/"):
        drift.append("register_url")
    if not product.is_published or product.status != ProductStatus.GA:
        drift.append("publish/status")

    fixed = 0
    if fix and drift:
        product.name = CORETRUST_NAME
        product.external_app_url = expected_app
        product.demo_url = expected_demo
        product.register_url = expected_register
        product.is_published = True
        product.status = ProductStatus.GA
        product.save(
            update_fields=[
                "name",
                "external_app_url",
                "demo_url",
                "register_url",
                "is_published",
                "status",
                "updated_at",
            ]
        )
        fixed = 1

    return Finding(
        code="coretrust_catalog",
        severity="warning" if drift else "info",
        message=(
            "CoreTrust catalog OK"
            if not drift
            else f"CoreTrust drift: {', '.join(drift)}" + ("; repaired" if fixed else "")
        ),
        count=len(drift),
        sample_ids=[str(product.pk)],
        fixed=fixed,
    )


def _replace_legacy_name(value: str) -> str:
    if not value:
        return value
    return (
        value.replace(LEGACY_NAME, CORETRUST_NAME)
        .replace("microfinance core", "CoreTrust")
        .replace("Microfinance core", "CoreTrust")
    )


def check_stale_microfinance_copy(*, fix: bool = False) -> Finding:
    """Rewrite published CMS/docs still using legacy Microfinance Core wording."""
    from cms.models import FAQ, PageSection, SectionItem
    from documentation.models import DocArticle

    needles = (LEGACY_NAME, "microfinance core")
    hits = 0
    fixed = 0
    samples: list[str] = []

    def _needle_q(fields):
        q = Q()
        for field_name in fields:
            for needle in needles:
                q |= Q(**{f"{field_name}__icontains": needle})
        return q

    targets = [
        ("doc", DocArticle.objects.filter(_needle_q(("title", "excerpt", "body")), is_published=True), ("title", "excerpt", "body")),
        ("faq", FAQ.objects.filter(_needle_q(("question", "answer")), is_published=True), ("question", "answer")),
        (
            "section_item",
            SectionItem.objects.filter(_needle_q(("title", "subtitle", "description")), is_active=True),
            ("title", "subtitle", "description"),
        ),
        (
            "section",
            PageSection.objects.filter(_needle_q(("title", "subtitle", "body")), is_active=True),
            ("title", "subtitle", "body"),
        ),
    ]

    # Marketing stories may still use the legacy product name.
    try:
        from marketing.models import SuccessStory

        targets.append(
            (
                "story",
                SuccessStory.objects.filter(
                    _needle_q(("title", "excerpt", "body", "quote")), is_published=True
                ),
                ("title", "excerpt", "body", "quote"),
            )
        )
    except Exception:
        pass

    for prefix, qs, fields in targets:
        c = qs.count()
        hits += c
        samples.extend(f"{prefix}:{pk}" for pk in qs.values_list("pk", flat=True)[:3])
        if not fix or c == 0:
            continue
        for obj in qs:
            changed = []
            for field_name in fields:
                old = getattr(obj, field_name) or ""
                new = _replace_legacy_name(old)
                if new != old:
                    setattr(obj, field_name, new)
                    changed.append(field_name)
            if changed:
                if hasattr(obj, "updated_at"):
                    changed.append("updated_at")
                obj.save(update_fields=changed)
                fixed += 1

    return Finding(
        code="stale_microfinance_copy",
        severity="warning" if hits else "info",
        message=(
            f"{hits} published content row(s) still mention Microfinance Core"
            + (f"; rewritten {fixed}" if fix else "")
        ),
        count=hits,
        sample_ids=samples[:8],
        fixed=fixed,
    )


def check_expire_trials(*, fix: bool = False) -> Finding:
    overdue = Subscription.objects.filter(
        status=SubscriptionStatus.TRIAL,
        trial_ends_at__lt=timezone.now().date(),
    )
    count = overdue.count()
    fixed = 0
    if fix and count:
        fixed = expire_due_trials()
    return Finding(
        code="overdue_trials",
        severity="warning" if count else "info",
        message=(
            f"{count} overdue trial subscription(s)"
            + (f"; expired {fixed}" if fix else "")
        ),
        count=count,
        sample_ids=_sample_ids(overdue),
        fixed=fixed,
    )


UNSUPPORTED_TRUST_PHRASES = (
    "global organizations trust",
    "trusted by industry leaders",
    "organizations trust worldwide",
    "hospital management 2.0",
    "14-day free trial",
    "14-day trial",
    "14 day trial",
    "free trial on every plan",
    "every product offers a free trial",
)


def check_unsupported_marketing_claims(*, fix: bool = False) -> Finding:
    """Flag (and optionally scrub) slogans/posts that outrun public proof."""
    from cms.models import HeroBanner, PageSection, SectionItem
    from marketing.models import BlogPost, CaseStudy, SuccessStory

    hits = 0
    fixed = 0
    samples: list[str] = []

    for banner in HeroBanner.objects.all():
        blob = " ".join(
            [
                banner.eyebrow or "",
                banner.headline or "",
                banner.subheadline or "",
                banner.trust_text or "",
            ]
        ).lower()
        if any(p in blob for p in UNSUPPORTED_TRUST_PHRASES):
            hits += 1
            samples.append(f"hero:{banner.pk}")
            if fix:
                for field in ("eyebrow", "headline", "subheadline", "trust_text"):
                    value = getattr(banner, field) or ""
                    lower = value.lower()
                    if "global organizations trust" in lower:
                        setattr(
                            banner,
                            field,
                            "Enterprise software for organizations that scale.",
                        )
                    elif "trusted by industry leaders" in lower:
                        setattr(banner, field, "Built for serious operations")
                banner.save()
                fixed += 1

    hospital_posts = BlogPost.objects.filter(
        Q(title__icontains="Hospital Management 2.0")
        | Q(slug="introducing-hospital-management-2-0")
    )
    hits += hospital_posts.count()
    samples.extend(f"blog:{pk}" for pk in hospital_posts.values_list("pk", flat=True)[:3])
    if fix and hospital_posts.exists():
        from django.utils import timezone

        roadmap_title = "Inside Zreta's Hospital Management Roadmap"
        roadmap_excerpt = (
            "What Hospital Management is planned to cover on Zreta — "
            "not a live product release announcement."
        )
        roadmap_body = (
            "Hospital Management is on the Zreta roadmap.\n\n"
            "We are exploring appointments, billing, and clinical workflows for clinics "
            "and hospitals. This article is a roadmap note, not a generally-available release.\n\n"
            "ChurchHub and CoreTrust are the live products on Zreta today. Hospital Management "
            "remains Coming soon until we publish it as live."
        )
        target_slug = "inside-zretas-hospital-management-roadmap"
        primary = hospital_posts.first()
        primary.title = roadmap_title
        primary.slug = target_slug
        primary.excerpt = roadmap_excerpt
        primary.body = roadmap_body
        if hasattr(primary, "meta_title"):
            primary.meta_title = roadmap_title
        if hasattr(primary, "meta_description"):
            primary.meta_description = roadmap_excerpt
        primary.is_featured = False
        primary.is_published = True
        if not primary.published_at:
            primary.published_at = timezone.now()
        primary.save()
        fixed += 1
        hospital_posts.exclude(pk=primary.pk).update(is_published=False, is_featured=False)

    seeded_stories = SuccessStory.objects.filter(
        Q(slug="unity-microfinance-success") | Q(company__icontains="Unity"),
        is_published=True,
    )
    seeded_cases = CaseStudy.objects.filter(
        Q(slug="horizon-academy-case-study") | Q(client_name__icontains="Horizon"),
        is_published=True,
    )
    hits += seeded_stories.count() + seeded_cases.count()
    if fix:
        fixed += seeded_stories.update(is_published=False, is_featured=False)
        fixed += seeded_cases.update(is_published=False, is_featured=False)

    typo_products = Product.objects.filter(
        Q(long_description__contains="system..")
        | Q(short_description__contains="system..")
        | Q(tagline__contains="system..")
        | Q(long_description__contains="system.s")
        | Q(short_description__contains="system.s")
        | Q(tagline__contains="system.s")
    )
    hits += typo_products.count()
    if fix:
        for product in typo_products:
            for field in ("short_description", "long_description", "tagline"):
                value = getattr(product, field) or ""
                value = value.replace("system..", "system.").replace("system.s", "system.")
                setattr(product, field, value)
            product.save()
            fixed += 1

    return Finding(
        code="unsupported_marketing_claims",
        severity="warning" if hits else "info",
        message=(
            f"{hits} unsupported marketing claim / contradiction row(s)"
            + (f"; repaired {fixed}" if fix else "")
        ),
        count=hits,
        sample_ids=samples[:8],
        fixed=fixed,
    )


CHECKS: list[Callable[..., Finding]] = [
    check_null_organizations,
    check_license_org_alignment,
    check_cross_user_links,
    check_status_date_invariants,
    check_featured_products,
    check_coretrust_catalog,
    check_stale_microfinance_copy,
    check_unsupported_marketing_claims,
    check_expire_trials,
]


@transaction.atomic
def run_sanitization(*, fix: bool = False) -> SanitizeReport:
    report = SanitizeReport()
    for check in CHECKS:
        # Checks that only report ignore fix kw if not accepted
        try:
            finding = check(fix=fix)
        except TypeError:
            finding = check()
        report.add(finding)
    return report
