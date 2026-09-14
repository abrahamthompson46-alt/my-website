from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from api.permissions import HasOrganizationScope, resolve_request_organization


class OrganizationAPIMixin:
    """Resolve and require organization scope for tenant-owned resources."""

    permission_classes = [IsAuthenticated, HasOrganizationScope]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        organization = resolve_request_organization(request)
        if organization is None:
            raise PermissionDenied("Pass X-Organization-ID for tenant-scoped endpoints.")
        request.organization = organization

    def get_organization(self):
        return self.request.organization
