from django.contrib.auth.mixins import LoginRequiredMixin


class PortalLoginRequiredMixin(LoginRequiredMixin):
    """Base mixin for authenticated portal views."""

    login_url = "accounts:login"
