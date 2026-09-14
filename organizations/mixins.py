"""Mixins for organization-scoped views and models."""


class OrganizationQuerysetMixin:
    """
    Scope querysets to the active organization when available.
    Falls back to per-user filtering for legacy rows without an organization.
    """

    organization_field = "organization"
    user_field = "user"

    def get_queryset(self):
        qs = super().get_queryset()
        org = getattr(self.request, "organization", None)
        if org is not None:
            return qs.filter(**{self.organization_field: org})
        return qs.filter(**{self.user_field: self.request.user})
