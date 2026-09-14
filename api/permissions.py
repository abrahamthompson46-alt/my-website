"""API authentication and tenant permission helpers."""

from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework.permissions import BasePermission

from organizations.models import MembershipStatus, Organization
from organizations.services import get_membership


def resolve_request_organization(request):
    """
    Resolve tenant from X-Organization-ID / X-Organization-Slug headers.
    Returns None when no org header is provided.
    """
    org_id = request.headers.get("X-Organization-ID") or request.META.get("HTTP_X_ORGANIZATION_ID")
    org_slug = request.headers.get("X-Organization-Slug") or request.META.get("HTTP_X_ORGANIZATION_SLUG")
    if not org_id and not org_slug:
        return None

    qs = Organization.objects.filter(status="active")
    if org_id:
        organization = qs.filter(pk=org_id).first()
    else:
        organization = qs.filter(slug=org_slug).first()

    if not organization:
        raise PermissionDenied("Organization not found or inactive.")

    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        raise AuthenticationFailed("Authentication required for organization scope.")

    membership = get_membership(user, organization)
    if not membership or membership.status != MembershipStatus.ACTIVE:
        raise PermissionDenied("You are not a member of this organization.")

    request.organization = organization
    request.organization_membership = membership
    return organization


class HasOrganizationScope(BasePermission):
    """Require an authenticated membership in the requested organization."""

    message = "Active organization membership required. Pass X-Organization-ID."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        try:
            organization = resolve_request_organization(request)
        except (PermissionDenied, AuthenticationFailed):
            return False
        return organization is not None
