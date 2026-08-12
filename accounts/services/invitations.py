from django.db import transaction
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from accounts.models import StaffInvitation
from accounts.models.invitation import InvitationStatus
from accounts.services.rbac import assign_role
from control_room.services.email_delivery import send_platform_mail


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
    from common.services.email_branding import get_email_brand_context

    accept_url = request.build_absolute_uri(
        reverse("accounts:accept_invite", kwargs={"token": raw_token})
    )
    inviter = invitation.invited_by
    inviter_name = inviter.display_name if inviter else ""
    context = get_email_brand_context(
        {
            "invitation": invitation,
            "accept_url": accept_url,
            "inviter": inviter,
            "inviter_name": inviter_name or (inviter.email if inviter else ""),
            "invitation_ttl_hours": StaffInvitation.INVITATION_TTL_HOURS,
        }
    )
    subject = render_to_string("emails/staff_invite_subject.txt", context).strip()
    body = render_to_string("emails/staff_invite_body.txt", context)
    html_body = render_to_string("emails/staff_invite_body.html", context)
    send_platform_mail(
        subject=subject,
        message=body,
        recipient_list=[invitation.email],
        html_message=html_body,
        headers={"X-Email-Type": "staff-invitation"},
        fail_silently=False,
    )


def get_invitation_by_token(raw_token: str):
    if not raw_token:
        return None
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
        invitation.token_hash = StaffInvitation.burn_token()
        invitation.save(update_fields=["status", "token_hash", "updated_at"])
    return invitation if invitation.is_valid else invitation


@transaction.atomic
def accept_invitation(invitation, *, user):
    locked = StaffInvitation.objects.select_for_update().get(pk=invitation.pk)
    if not locked.is_valid:
        raise ValueError("This invitation is no longer valid.")

    if locked.grant_staff_access:
        user.is_staff = True
        user.save(update_fields=["is_staff"])

    assign_role(user, locked.role, assigned_by=locked.invited_by)

    locked.status = InvitationStatus.ACCEPTED
    locked.accepted_at = timezone.now()
    locked.accepted_user = user
    locked.token_hash = StaffInvitation.burn_token()
    locked.save(
        update_fields=["status", "accepted_at", "accepted_user", "token_hash", "updated_at"]
    )
    return user


def revoke_invitation(invitation):
    if invitation.status != InvitationStatus.PENDING:
        return False
    invitation.status = InvitationStatus.REVOKED
    invitation.token_hash = StaffInvitation.burn_token()
    invitation.save(update_fields=["status", "token_hash", "updated_at"])
    return True
