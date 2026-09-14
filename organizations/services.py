"""Organization / tenant services."""

from __future__ import annotations

from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from organizations.models import (
    MembershipRole,
    MembershipStatus,
    Organization,
    OrganizationMembership,
    OrganizationStatus,
)

ACTIVE_ORG_SESSION_KEY = "active_organization_id"

OWNER_ADMIN_ROLES = {MembershipRole.OWNER, MembershipRole.ADMIN}


def _unique_slug(name: str) -> str:
    base = slugify(name)[:180] or "org"
    candidate = base
    n = 1
    while Organization.objects.filter(slug=candidate).exists():
        n += 1
        candidate = f"{base}-{n}"
    return candidate


@transaction.atomic
def create_organization(*, name: str, created_by, slug: str | None = None) -> Organization:
    """Create an organization and make created_by the owner."""
    org = Organization.objects.create(
        name=name.strip() or f"{created_by.email}'s workspace",
        slug=slug or _unique_slug(name or created_by.email),
        status=OrganizationStatus.ACTIVE,
        created_by=created_by,
    )
    OrganizationMembership.objects.create(
        organization=org,
        user=created_by,
        role=MembershipRole.OWNER,
        status=MembershipStatus.ACTIVE,
        invited_by=created_by,
        joined_at=timezone.now(),
    )
    return org


@transaction.atomic
def ensure_default_organization(user, *, company: str = "") -> Organization:
    """
    Ensure the user has at least one active organization membership.
    Creates a personal workspace when none exists.
    """
    membership = (
        OrganizationMembership.objects.filter(
            user=user,
            status=MembershipStatus.ACTIVE,
            organization__status=OrganizationStatus.ACTIVE,
        )
        .select_related("organization")
        .order_by("created_at")
        .first()
    )
    if membership:
        return membership.organization

    name = (company or "").strip() or f"{user.display_name}'s workspace"
    return create_organization(name=name, created_by=user)


def get_user_memberships(user):
    return (
        OrganizationMembership.objects.filter(
            user=user,
            status=MembershipStatus.ACTIVE,
            organization__status=OrganizationStatus.ACTIVE,
        )
        .select_related("organization")
        .order_by("organization__name")
    )


def get_user_organizations(user):
    return [m.organization for m in get_user_memberships(user)]


def get_membership(user, organization) -> OrganizationMembership | None:
    if not user or not getattr(user, "is_authenticated", False) or not organization:
        return None
    return (
        OrganizationMembership.objects.filter(
            user=user,
            organization=organization,
            status=MembershipStatus.ACTIVE,
        )
        .select_related("organization")
        .first()
    )


def user_can_manage_organization(user, organization) -> bool:
    membership = get_membership(user, organization)
    return bool(membership and membership.role in OWNER_ADMIN_ROLES)


def resolve_active_organization(request):
    """Resolve the active tenant for this request from session or first membership."""
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return None

    memberships = list(get_user_memberships(user))
    if not memberships:
        return None

    org_ids = {str(m.organization_id): m.organization for m in memberships}
    session_org_id = request.session.get(ACTIVE_ORG_SESSION_KEY)
    if session_org_id and str(session_org_id) in org_ids:
        return org_ids[str(session_org_id)]

    org = memberships[0].organization
    request.session[ACTIVE_ORG_SESSION_KEY] = str(org.pk)
    return org


def set_active_organization(request, organization) -> bool:
    """Switch the active organization if the user is an active member."""
    if not get_membership(request.user, organization):
        return False
    request.session[ACTIVE_ORG_SESSION_KEY] = str(organization.pk)
    request.organization = organization
    return True


def add_member(*, organization, user, role=MembershipRole.MEMBER, invited_by=None):
    membership, created = OrganizationMembership.objects.get_or_create(
        organization=organization,
        user=user,
        defaults={
            "role": role,
            "status": MembershipStatus.ACTIVE,
            "invited_by": invited_by,
            "joined_at": timezone.now(),
        },
    )
    if not created and membership.status != MembershipStatus.ACTIVE:
        membership.status = MembershipStatus.ACTIVE
        membership.role = role
        membership.joined_at = membership.joined_at or timezone.now()
        membership.save(update_fields=["status", "role", "joined_at", "updated_at"])
    return membership
