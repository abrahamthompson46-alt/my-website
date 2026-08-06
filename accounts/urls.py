from django.urls import path
from django.contrib.auth import views as auth_views

from accounts.views import (
    EnterprisePasswordResetConfirmView,
    EnterprisePasswordResetView,
    LoggedOutView,
    MFABackupCodesView,
    MFADisableView,
    MFAEnrollView,
    MFAVerifyView,
    PortalLoginView,
    PortalLogoutView,
    RevokeOtherSessionsView,
    SessionRevokeView,
    VerifyEmailPromptView,
    VerifyEmailView,
)

app_name = "accounts"

urlpatterns = [
    path("login/", PortalLoginView.as_view(), name="login"),
    path("logout/", PortalLogoutView.as_view(), name="logout"),
    path("logged-out/", LoggedOutView.as_view(), name="logged_out"),
    path("password-reset/", EnterprisePasswordResetView.as_view(), name="password_reset"),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(template_name="accounts/password_reset_done.html"),
        name="password_reset_done",
    ),
    path(
        "password-reset/confirm/<uidb64>/<token>/",
        EnterprisePasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "password-reset/complete/",
        auth_views.PasswordResetCompleteView.as_view(template_name="accounts/password_reset_complete.html"),
        name="password_reset_complete",
    ),
    path(
        "password-change/",
        auth_views.PasswordChangeView.as_view(
            template_name="accounts/password_change.html",
            success_url="/app/security/",
        ),
        name="password_change",
    ),
    path("verify-email/<str:token>/", VerifyEmailView.as_view(), name="verify_email"),
    path("verify-email/", VerifyEmailPromptView.as_view(), name="verify_email_prompt"),
    path("sessions/<uuid:session_id>/revoke/", SessionRevokeView.as_view(), name="session_revoke"),
    path("sessions/revoke-others/", RevokeOtherSessionsView.as_view(), name="sessions_revoke_others"),
    path("mfa/verify/", MFAVerifyView.as_view(), name="mfa_verify"),
    path("mfa/enroll/", MFAEnrollView.as_view(), name="mfa_enroll"),
    path("mfa/backup-codes/", MFABackupCodesView.as_view(), name="mfa_backup_codes"),
    path("mfa/disable/", MFADisableView.as_view(), name="mfa_disable"),
]
