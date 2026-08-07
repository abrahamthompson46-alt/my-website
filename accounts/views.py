from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordResetConfirmView,
    PasswordResetView,
)
from django.contrib.auth import get_user_model
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils import timezone
from django.views.generic import TemplateView, View

from accounts.backends import record_failed_login, reset_failed_login
from accounts.forms import (
    EnterprisePasswordResetForm,
    EnterpriseSetPasswordForm,
    MFAChallengeForm,
    MFAEnrollConfirmForm,
    MFADisableForm,
    PortalLoginForm,
)
from accounts.models import AuditEventType, MFAMethod
from accounts.services.audit import log_audit_event
from accounts.services.email import get_or_create_security_profile, send_verification_email
from accounts.services.mfa import (
    disable_mfa,
    enable_totp,
    generate_backup_codes,
    generate_totp_secret,
    provisioning_uri,
    verify_mfa_code,
    verify_totp,
)
from accounts.services.rate_limit import check_auth_rate_limit, log_rate_limit_exceeded, reset_auth_rate_limit
from accounts.services.sessions import revoke_other_sessions, revoke_session, track_user_session
from customer_portal.mixins import PortalMixin

User = get_user_model()


class PortalLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = PortalLoginForm
    redirect_authenticated_user = True

    def dispatch(self, request, *args, **kwargs):
        if request.method == "POST" and check_auth_rate_limit(request, "login", limit=10, window_seconds=900):
            log_rate_limit_exceeded(request, "login")
            messages.error(request, "Too many login attempts. Please try again later.")
            return redirect("accounts:login")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        email = form.cleaned_data.get("username", "")
        if check_auth_rate_limit(
            request=self.request, scope="login-email", identifier=email, limit=5, window_seconds=900
        ):
            log_rate_limit_exceeded(self.request, "login-email")
            messages.error(self.request, "Too many failed attempts for this account. Please try again later.")
            return redirect("accounts:login")

        user = form.get_user()
        reset_failed_login(user)
        reset_auth_rate_limit(self.request, "login")
        reset_auth_rate_limit(self.request, "login-email", email)

        profile = get_or_create_security_profile(user)
        if profile.mfa_enabled and profile.mfa_method == MFAMethod.TOTP:
            self.request.session["mfa_pending_user_id"] = str(user.pk)
            self.request.session["mfa_auth_backend"] = getattr(
                user, "backend", settings.AUTHENTICATION_BACKENDS[0]
            )
            self.request.session["mfa_next"] = _post_login_url(user)
            return redirect("accounts:mfa_verify")

        auth_login(self.request, user)
        track_user_session(self.request, user)
        log_audit_event(AuditEventType.LOGIN_SUCCESS, request=self.request, user=user)
        return redirect(self.get_success_url())

    def get_success_url(self):
        explicit = self.request.POST.get("next") or self.request.GET.get("next")
        if explicit and url_has_allowed_host_and_scheme(
            url=explicit,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return explicit
        user = getattr(self.request, "user", None)
        if user and user.is_authenticated and user.is_staff:
            return reverse("control_room:dashboard")
        return reverse("customer_portal:dashboard")

    def form_invalid(self, form):
        email = self.request.POST.get("username", "")
        record_failed_login(self.request, email)
        log_audit_event(
            AuditEventType.LOGIN_FAILED,
            request=self.request,
            message=f"Failed login for {email}",
            metadata={"email": email},
        )
        return super().form_invalid(form)


class PortalLogoutView(LogoutView):
    next_page = reverse_lazy("accounts:logged_out")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            log_audit_event(AuditEventType.LOGOUT, request=request, user=request.user)
        return super().dispatch(request, *args, **kwargs)


class LoggedOutView(TemplateView):
    template_name = "accounts/logged_out.html"


class EnterprisePasswordResetView(PasswordResetView):
    template_name = "accounts/password_reset.html"
    email_template_name = "accounts/email/password_reset_body.txt"
    subject_template_name = "accounts/email/password_reset_subject.txt"
    html_email_template_name = "accounts/email/password_reset_body.html"
    form_class = EnterprisePasswordResetForm
    success_url = reverse_lazy("accounts:password_reset_done")

    def dispatch(self, request, *args, **kwargs):
        if request.method == "POST" and check_auth_rate_limit(request, "password-reset", limit=5, window_seconds=3600):
            log_rate_limit_exceeded(request, "password-reset")
            messages.error(request, "Too many reset requests. Please try again later.")
            return redirect("accounts:password_reset")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        log_audit_event(
            AuditEventType.PASSWORD_RESET_REQUESTED,
            request=self.request,
            message=f"Reset requested for {form.cleaned_data['email']}",
            metadata={"email": form.cleaned_data["email"]},
        )
        return response


class EnterprisePasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    form_class = EnterpriseSetPasswordForm
    success_url = reverse_lazy("accounts:password_reset_complete")

    def form_valid(self, form):
        response = super().form_valid(form)
        profile = get_or_create_security_profile(form.user)
        profile.password_changed_at = timezone.now()
        profile.must_reset_password = False
        profile.save(update_fields=["password_changed_at", "must_reset_password", "updated_at"])
        log_audit_event(
            AuditEventType.PASSWORD_RESET_COMPLETED,
            request=self.request,
            user=form.user,
        )
        return response


class VerifyEmailView(View):
    def get(self, request, token):
        from accounts.services.email import verify_email_token

        user = verify_email_token(token)
        if user:
            log_audit_event(AuditEventType.EMAIL_VERIFIED, request=request, user=user)
            messages.success(request, "Your email has been verified.")
            if request.user.is_authenticated and request.user.pk == user.pk:
                return redirect("customer_portal:security")
            return redirect("accounts:login")
        messages.error(request, "This verification link is invalid or has expired.")
        return redirect("accounts:verify_email_prompt")


class VerifyEmailPromptView(PortalMixin, TemplateView):
    template_name = "accounts/verify_email_prompt.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = get_or_create_security_profile(self.request.user)
        context["email_verified"] = profile.email_verified
        context["breadcrumb_items"] = [
            {"label": "Dashboard", "url_name": "customer_portal:dashboard"},
            {"label": "Verify Email"},
        ]
        return context

    def post(self, request, *args, **kwargs):
        if check_auth_rate_limit(request, "verify-email", limit=3, window_seconds=3600):
            messages.error(request, "Too many verification emails sent. Please wait before trying again.")
            return redirect("accounts:verify_email_prompt")
        send_verification_email(request, request.user)
        log_audit_event(AuditEventType.EMAIL_VERIFICATION_SENT, request=request, user=request.user)
        messages.success(request, "Verification email sent. Check your inbox.")
        return redirect("accounts:verify_email_prompt")


class SessionRevokeView(PortalMixin, View):
    def post(self, request, session_id):
        current_key = request.session.session_key
        session = revoke_session(request.user, session_id, current_session_key=current_key)
        if session:
            log_audit_event(
                AuditEventType.SESSION_REVOKED,
                request=request,
                user=request.user,
                metadata={"session_id": str(session_id)},
            )
            messages.success(request, "Session revoked.")
        else:
            messages.error(request, "Session not found.")
        return redirect("customer_portal:security")


class RevokeOtherSessionsView(PortalMixin, View):
    def post(self, request):
        revoke_other_sessions(request.user, request.session.session_key)
        log_audit_event(AuditEventType.SESSION_REVOKED, request=request, user=request.user, message="Revoked all other sessions")
        messages.success(request, "All other sessions have been signed out.")
        return redirect("customer_portal:security")


class MFAVerifyView(View):
    template_name = "accounts/mfa_verify.html"

    def get(self, request):
        if not request.session.get("mfa_pending_user_id"):
            return redirect("accounts:login")
        return render(request, self.template_name, {"form": MFAChallengeForm()})

    def post(self, request):
        if check_auth_rate_limit(request, "mfa-verify", limit=10, window_seconds=900):
            log_rate_limit_exceeded(request, "mfa-verify")
            messages.error(request, "Too many verification attempts. Please try again later.")
            return redirect("accounts:login")

        user_id = request.session.get("mfa_pending_user_id")
        if not user_id:
            return redirect("accounts:login")

        user = User.objects.filter(pk=user_id, is_active=True).first()
        if not user:
            request.session.pop("mfa_pending_user_id", None)
            return redirect("accounts:login")

        form = MFAChallengeForm(request.POST)
        if form.is_valid():
            profile = get_or_create_security_profile(user)
            if verify_mfa_code(profile, form.cleaned_data["code"]):
                backend = request.session.get("mfa_auth_backend", settings.AUTHENTICATION_BACKENDS[0])
                auth_login(request, user, backend=backend)
                track_user_session(request, user)
                reset_auth_rate_limit(request, "mfa-verify")
                log_audit_event(AuditEventType.MFA_CHALLENGE, request=request, user=user, message="MFA verified")
                log_audit_event(AuditEventType.LOGIN_SUCCESS, request=request, user=user)
                next_url = request.session.pop("mfa_next", None) or _post_login_url(user)
                request.session.pop("mfa_pending_user_id", None)
                request.session.pop("mfa_auth_backend", None)
                if next_url and not url_has_allowed_host_and_scheme(
                    url=next_url,
                    allowed_hosts={request.get_host()},
                    require_https=request.is_secure(),
                ):
                    next_url = _post_login_url(user)
                return redirect(next_url)
            record_failed_login(request, user.email)
            form.add_error("code", "Invalid authentication code.")

        return render(request, self.template_name, {"form": form})


class MFAEnrollView(PortalMixin, View):
    template_name = "accounts/mfa_enroll.html"

    def get(self, request):
        profile = get_or_create_security_profile(request.user)
        if profile.mfa_enabled:
            return redirect("customer_portal:security")

        secret = request.session.get("mfa_enroll_secret")
        if not secret:
            secret = generate_totp_secret()
            request.session["mfa_enroll_secret"] = secret

        qr_data_uri = _totp_qr_data_uri(provisioning_uri(request.user, secret))
        return render(
            request,
            self.template_name,
            {
                "form": MFAEnrollConfirmForm(),
                "secret": secret,
                "qr_data_uri": qr_data_uri,
                "breadcrumb_items": [
                    {"label": "Dashboard", "url_name": "customer_portal:dashboard"},
                    {"label": "Security", "url_name": "customer_portal:security"},
                    {"label": "Enable MFA"},
                ],
            },
        )

    def post(self, request):
        secret = request.session.get("mfa_enroll_secret")
        if not secret:
            messages.error(request, "Enrollment session expired. Please start again.")
            return redirect("accounts:mfa_enroll")

        form = MFAEnrollConfirmForm(request.POST)
        if form.is_valid() and verify_totp(secret, form.cleaned_data["code"]):
            plain_codes, hashed_codes = generate_backup_codes()
            enable_totp(request.user, secret, hashed_codes, request=request)
            request.session.pop("mfa_enroll_secret", None)
            request.session["mfa_backup_codes"] = plain_codes
            return redirect("accounts:mfa_backup_codes")

        qr_data_uri = _totp_qr_data_uri(provisioning_uri(request.user, secret))
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "secret": secret,
                "qr_data_uri": qr_data_uri,
                "breadcrumb_items": [
                    {"label": "Dashboard", "url_name": "customer_portal:dashboard"},
                    {"label": "Security", "url_name": "customer_portal:security"},
                    {"label": "Enable MFA"},
                ],
            },
        )


class MFABackupCodesView(PortalMixin, View):
    template_name = "accounts/mfa_backup_codes.html"

    def get(self, request):
        codes = request.session.pop("mfa_backup_codes", None)
        if not codes:
            return redirect("customer_portal:security")
        return render(
            request,
            self.template_name,
            {
                "backup_codes": codes,
                "breadcrumb_items": [
                    {"label": "Dashboard", "url_name": "customer_portal:dashboard"},
                    {"label": "Security", "url_name": "customer_portal:security"},
                    {"label": "Backup Codes"},
                ],
            },
        )


class MFADisableView(PortalMixin, View):
    def post(self, request):
        form = MFADisableForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Could not disable MFA. Check your password and try again.")
            return redirect("customer_portal:security")

        if not request.user.check_password(form.cleaned_data["password"]):
            messages.error(request, "Incorrect password.")
            return redirect("customer_portal:security")

        profile = get_or_create_security_profile(request.user)
        code = form.cleaned_data.get("code", "").strip()
        if profile.mfa_enabled:
            if not code:
                messages.error(request, "Enter your authentication or backup code to disable MFA.")
                return redirect("customer_portal:security")
            if not verify_mfa_code(profile, code):
                messages.error(request, "Invalid authentication code.")
                return redirect("customer_portal:security")

        disable_mfa(request.user, request=request)
        messages.success(request, "Multi-factor authentication has been disabled.")
        return redirect("customer_portal:security")


def _post_login_url(user):
    if user.is_staff:
        return reverse("control_room:dashboard")
    return reverse("customer_portal:dashboard")


def _totp_qr_data_uri(data: str) -> str:
    import base64
    import io

    import qrcode

    buffer = io.BytesIO()
    qrcode.make(data).save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"
