from organizations.services import get_user_memberships


def organization_context(request):
    org = getattr(request, "organization", None)
    membership = getattr(request, "organization_membership", None)
    memberships = []
    user = getattr(request, "user", None)
    if user and user.is_authenticated:
        memberships = list(get_user_memberships(user))
    return {
        "current_organization": org,
        "current_organization_membership": membership,
        "user_organization_memberships": memberships,
    }
