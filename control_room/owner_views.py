"""Platform owner tools — email setup and operational settings."""

from django.contrib import messages
from django.conf import settings
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.generic import TemplateView

from control_room.forms import PlatformEmailSettingsForm
from control_room.mixins import PlatformOwnerMixin
from control_room.models import PlatformOperationsSettings
from control_room.services import log_control_change
from control_room.services.email_delivery import (
    EmailConfigurationError,
    get_email_status_summary,
    send_platform_mail,
)


class PlatformOpsView(PlatformOwnerMixin, TemplateView):
    help_key = "platform_ops"
    template_name = "control_room/platform_ops.html"

    def get_ops_settings(self):
        return PlatformOperationsSettings.load()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ops = self.get_ops_settings()
        context["breadcrumb_items"] = [
            {"label": "Command Center", "url_name": "control_room:dashboard"},
            {"label": "Platform Ops"},
        ]
        context["ops_settings"] = ops
        context["email_form"] = kwargs.get("email_form", PlatformEmailSettingsForm(instance=ops))
        context["email_status"] = get_email_status_summary()
        context["env_email_backend"] = self.request.environ.get("EMAIL_BACKEND", "")
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        ops = self.get_ops_settings()

        if action == "save_email":
            form = PlatformEmailSettingsForm(request.POST, instance=ops)
            if not form.is_valid():
                return self.render_to_response(self.get_context_data(email_form=form))
            form.save()
            log_control_change(
                request.user,
                area="platform_ops",
                action="update_email",
                summary="Updated platform email settings",
            )
            messages.success(request, "Email settings saved.")
            return redirect("control_room:platform_ops")

        if action == "test_email":
            try:
                send_platform_mail(
                    subject="Platform email test",
                    message=render_to_string(
                        "emails/platform_test_body.txt",
                        {"site_name": settings.SITE_NAME},
                    ).strip(),
                    recipient_list=[request.user.email],
                )
            except EmailConfigurationError as exc:
                ops.last_email_test_at = timezone.now()
                ops.last_email_test_status = "failed"
                ops.last_email_test_message = str(exc)
                ops.save(update_fields=["last_email_test_at", "last_email_test_status", "last_email_test_message", "updated_at"])
                messages.error(request, str(exc))
                return redirect("control_room:platform_ops")
            except Exception as exc:
                ops.last_email_test_at = timezone.now()
                ops.last_email_test_status = "failed"
                ops.last_email_test_message = str(exc)
                ops.save(update_fields=["last_email_test_at", "last_email_test_status", "last_email_test_message", "updated_at"])
                messages.error(request, f"Test email failed: {exc}")
                return redirect("control_room:platform_ops")

            ops.last_email_test_at = timezone.now()
            ops.last_email_test_status = "success"
            ops.last_email_test_message = f"Sent test email to {request.user.email}."
            ops.save(update_fields=["last_email_test_at", "last_email_test_status", "last_email_test_message", "updated_at"])
            messages.success(request, f"Test email sent to {request.user.email}.")
            return redirect("control_room:platform_ops")

        if action == "deploy":
            log_control_change(
                request.user,
                area="platform_ops",
                action="deploy_blocked",
                summary="Web-triggered deployment is disabled; use VPS deployment procedure",
            )
            messages.error(
                request,
                "Web-triggered deployment has been disabled for security. "
                "Use the controlled VPS procedure documented in docs/ZRETA_DEPLOYMENT_PROCEDURE.md.",
            )
            return redirect("control_room:platform_ops")

        messages.error(request, "Unknown action.")
        return redirect("control_room:platform_ops")
