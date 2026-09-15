"""Platform sanitization: report and repair DB/UI consistency issues."""

from __future__ import annotations

from dataclasses import dataclass, field
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


PURCHASABLE_STATUSES = frozenset({ProductStatus.GA, ProductStatus.BETA})
CORETRUST_SLUG = "microfinance-core"
CORETRUST_NAME = "CoreTrust"


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


def check_cross_user_links() -> Finding:
    """Report invoices/licenses whose user differs from linked subscription user."""
    invoice_qs = Invoice.objects.filter(subscription__isnull=False).exclude(
        user_id=F("subscription__user_id")
    )
    license_qs = License.objects.filter(subscription__isnull=False).exclude(
        user_id=F("subscription__user_id")
    )
    count = invoice_qs.count() + license_qs.count()
    samples = [f"invoice:{pk}" for pk in invoice_qs.values_list("pk", flat=True)[:4]]
    samples += [f"license:{pk}" for pk in license_qs.values_list("pk", flat=True)[:4]]
    return Finding(
        code="cross_user_link",
        severity="error" if count else "info",
        message=f"{count} invoice/license row(s) linked across different users (report-only)",
        count=count,
        sample_ids=samples,
    )


def check_status_date_invariants() -> Finding:
    """Impossible status/date combinations (report-only)."""
    checks = [
        Subscription.objects.filter(
            status=SubscriptionStatus.TRIAL, trial_ends_at__isnull=True
        ),
        Subscription.objects.filter(
            status=SubscriptionStatus.CANCELLED, cancelled_at__isnull=True
        ),
        Invoice.objects.filter(status=InvoiceStatus.PAID, paid_at__isnull=True),
        Payment.objects.filter(status=PaymentStatus.SUCCEEDED, paid_at__isnull=True),
        License.objects.filter(
            status=LicenseStatus.ACTIVE,
            subscription__status=SubscriptionStatus.EXPIRED,
        ),
    ]
    total = 0
    samples: list[str] = []
    for qs in checks:
        c = qs.count()
        total += c
        if c:
            samples.extend(_sample_ids(qs, limit=2))
    return Finding(
        code="status_date_invariant",
        severity="warning" if total else "info",
        message=f"{total} status/date contradiction(s) (report-only)",
        count=total,
        sample_ids=samples[:8],
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

    drift = []
    if product.name != CORETRUST_NAME:
        drift.append(f"name={product.name!r}")
    if not product.external_app_url:
        drift.append("missing external_app_url")
    if product.name == "Microfinance Core":
        drift.append("legacy Microfinance Core name")

    fixed = 0
    if fix and drift:
        product.name = CORETRUST_NAME
        if not product.external_app_url:
            product.external_app_url = "https://micro.zreta.com/"
        if not product.demo_url:
            product.demo_url = "https://micro.zreta.com/"
        product.is_published = True
        product.status = ProductStatus.GA
        product.save(
            update_fields=[
                "name",
                "external_app_url",
                "demo_url",
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
            else f"CoreTrust drift: {', '.join(drift)}" + ("; repaired" if fix else "")
        ),
        count=len(drift),
        sample_ids=[str(product.pk)],
        fixed=fixed,
    )


def check_stale_microfinance_copy() -> Finding:
    """Report published CMS/docs still using legacy Microfinance Core wording."""
    from cms.models import FAQ, PageSection, SectionItem
    from documentation.models import DocArticle

    needles = ("Microfinance Core", "microfinance core")
    hits = 0
    samples: list[str] = []

    def _needle_q(fields):
        q = Q()
        for field_name in fields:
            for needle in needles:
                q |= Q(**{f"{field_name}__icontains": needle})
        return q

    doc_qs = DocArticle.objects.filter(_needle_q(("title", "excerpt", "body")), is_published=True)
    faq_qs = FAQ.objects.filter(_needle_q(("question", "answer")), is_published=True)
    item_qs = SectionItem.objects.filter(
        _needle_q(("title", "subtitle", "description")), is_active=True
    )
    section_qs = PageSection.objects.filter(
        _needle_q(("title", "subtitle", "body")), is_active=True
    )

    for prefix, qs in (
        ("doc", doc_qs),
        ("faq", faq_qs),
        ("section_item", item_qs),
        ("section", section_qs),
    ):
        c = qs.count()
        hits += c
        samples.extend(f"{prefix}:{pk}" for pk in qs.values_list("pk", flat=True)[:3])

    return Finding(
        code="stale_microfinance_copy",
        severity="warning" if hits else "info",
        message=f"{hits} published content row(s) still mention Microfinance Core (report-only)",
        count=hits,
        sample_ids=samples[:8],
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


CHECKS: list[Callable[..., Finding]] = [
    check_null_organizations,
    check_license_org_alignment,
    check_cross_user_links,
    check_status_date_invariants,
    check_featured_products,
    check_coretrust_catalog,
    check_stale_microfinance_copy,
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
