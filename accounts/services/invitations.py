from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from accounts.models import StaffInvitation
from accounts.models.invitation import InvitationStatus
from accounts.services.rbac import assign_role


def create_staff_invitation(*, email, role, invited_by, grant_staff_access=True, message=""):
    raw_token = StaffInvitation.generate_token()
    invitation = StaffInvitation.objects.create(
        email=email.lower().strip(),
        role=role,
        invited_by=invited_by,
        token_hash=StaffInvitation.hash_token(raw_token),
        grant_staff_access=grant_staff_access,
        expires_at=StaffInvitation.default_expiry(),
        message=message,
    )
    return invitation, raw_token


def send_invitation_email(request, invitation, raw_token):
    accept_url = request.build_absolute_uri(
        reverse("accounts:accept_invite", kwargs={"token": raw_token})
    )
    context = {
        "invitation": invitation,
        "accept_url": accept_url,
        "inviter": invitation.invited_by,
        "site_name": getattr(settings, "SITE_NAME", "Platform"),
    }
    subject = render_to_string("emails/staff_invite_subject.txt", context).strip()
    body = render_to_string("emails/staff_invite_body.txt", context)
    send_mail(
        subject,
        body,
        settings.DEFAULT_FROM_EMAIL,
        [invitation.email],
        fail_silently=False,
    )


def get_invitation_by_token(raw_token: str):
    token_hash = StaffInvitation.hash_token(raw_token)
    invitation = (
        StaffInvitation.objects.select_related("role", "invited_by")
        .filter(token_hash=token_hash)
        .first()
    )
    if not invitation:
        return None
    if invitation.status == InvitationStatus.PENDING and invitation.expires_at <= timezone.now():
        invitation.status = InvitationStatus.EXPIRED
        invitation.save(update_fields=["status", "updated_at"])
    return invitation if invitation.is_valid else invitation


def accept_invitation(invitation, *, user):
    if not invitation.is_valid:
        raise ValueError("This invitation is no longer valid.")

    if invitation.grant_staff_access:
        user.is_staff = True
        user.save(update_fields=["is_staff"])

    assign_role(user, invitation.role, assigned_by=invitation.invited_by)

    invitation.status = InvitationStatus.ACCEPTED
    invitation.accepted_at = timezone.now()
    invitation.accepted_user = user
    invitation.save(update_fields=["status", "accepted_at", "accepted_user", "updated_at"])
    return user


def revoke_invitation(invitation):
    if invitation.status != InvitationStatus.PENDING:
        return False
    invitation.status = InvitationStatus.REVOKED
    invitation.save(update_fields=["status", "updated_at"])
    return True
