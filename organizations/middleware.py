from django.utils.deprecation import MiddlewareMixin

from organizations.services import resolve_active_organization


class ActiveOrganizationMiddleware(MiddlewareMixin):
    """Attach request.organization for authenticated customer tenants."""

    def process_request(self, request):
        request.organization = None
        request.organization_membership = None
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return None

        # Platform staff in ops/control keep platform-wide scope unless acting as a customer.
        path = request.path or ""
        if user.is_staff and (path.startswith("/ops/") or path.startswith("/control/") or path.startswith("/admin/")):
            return None

        org = resolve_active_organization(request)
        if org is None:
            from organizations.services import ACTIVE_ORG_SESSION_KEY, ensure_default_organization

            org = ensure_default_organization(user)
            request.session[ACTIVE_ORG_SESSION_KEY] = str(org.pk)

        request.organization = org
        if org:
            from organizations.services import get_membership

            request.organization_membership = get_membership(user, org)
        return None
