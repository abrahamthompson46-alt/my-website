"""Control Room team and role management."""

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView, FormView, ListView, View

from accounts.forms import AcceptInvitationForm, InviteUserForm, UserRoleAssignForm
from accounts.models import Role, StaffInvitation
from accounts.models.invitation import InvitationStatus
from accounts.services.invitations import (
    accept_invitation,
    create_staff_invitation,
    revoke_invitation,
    send_invitation_email,
)
from accounts.services.rbac import assign_role, remove_role
from control_room.mixins import TeamManagementMixin
from control_room.services import log_control_change

User = get_user_model()

STAFF_ROLES = ("platform-owner", "platform-admin", "support-agent", "billing-admin")


class TeamListView(TeamManagementMixin, ListView):
    help_key = "team"
    template_name = "control_room/team_list.html"
    context_object_name = "members"

    def get_queryset(self):
        return (
            User.objects.filter(is_staff=True)
            .prefetch_related("user_roles__role")
            .order_by("email")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_items"] = [
            {"label": "Command Center", "url_name": "control_room:dashboard"},
            {"label": "Team & Access"},
        ]
        context["pending_invitations"] = StaffInvitation.objects.filter(
            status=InvitationStatus.PENDING
        ).select_related("role", "invited_by")
        context["roles"] = Role.objects.filter(is_active=True).order_by("name")
        context["invite_form"] = kwargs.get("invite_form", InviteUserForm())
        return context

    def post(self, request, *args, **kwargs):
        form = InviteUserForm(request.POST)
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(invite_form=form))

        invitation, raw_token = create_staff_invitation(
            email=form.cleaned_data["email"],
            role=form.cleaned_data["role"],
            invited_by=request.user,
            grant_staff_access=form.cleaned_data["grant_staff_access"],
            message=form.cleaned_data.get("message", ""),
        )
        try:
            send_invitation_email(request, invitation, raw_token)
        except Exception as exc:
            messages.warning(request, f"Invite created but email failed: {exc}")

        log_control_change(
            request.user,
            area="team",
            action="invite",
            summary=f"Invited {invitation.email} as {invitation.role.name}",
        )
        messages.success(request, f"Invitation sent to {invitation.email}.")
        return redirect("control_room:team")


class TeamUserDetailView(TeamManagementMixin, DetailView):
    help_key = "team_user"
    model = User
    template_name = "control_room/team_user_detail.html"
    context_object_name = "member"

    def get_queryset(self):
        return User.objects.prefetch_related("user_roles__role", "user_roles__assigned_by")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        member = self.object
        context["breadcrumb_items"] = [
            {"label": "Command Center", "url_name": "control_room:dashboard"},
            {"label": "Team & Access", "url_name": "control_room:team"},
            {"label": member.email},
        ]
        context["assign_form"] = UserRoleAssignForm(
            initial={"is_staff": member.is_staff},
        )
        context["available_roles"] = Role.objects.filter(is_active=True).order_by("name")
        context["assigned_role_ids"] = set(member.user_roles.values_list("role_id", flat=True))
        return context


class TeamAssignRoleView(TeamManagementMixin, View):
    def post(self, request, pk):
        member = get_object_or_404(User, pk=pk)
        form = UserRoleAssignForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Invalid role selection.")
            return redirect("control_room:team_user", pk=pk)

        role = form.cleaned_data["role"]
        assign_role(member, role, assigned_by=request.user)

        if form.cleaned_data.get("is_staff"):
            member.is_staff = True
            member.save(update_fields=["is_staff", "updated_at"])

        log_control_change(
            request.user,
            area="team",
            action="assign_role",
            summary=f"Assigned {role.name} to {member.email}",
        )
        messages.success(request, f"Role {role.name} assigned to {member.email}.")
        return redirect("control_room:team_user", pk=pk)


class TeamRemoveRoleView(TeamManagementMixin, View):
    def post(self, request, pk, role_pk):
        member = get_object_or_404(User, pk=pk)
        role = get_object_or_404(Role, pk=role_pk)
        if role.slug == "platform-owner" and not request.user.is_superuser:
            messages.error(request, "Only a superuser can remove the Platform Owner role.")
            return redirect("control_room:team_user", pk=pk)

        remove_role(member, role)
        log_control_change(
            request.user,
            area="team",
            action="remove_role",
            summary=f"Removed {role.name} from {member.email}",
        )
        messages.success(request, f"Removed {role.name} from {member.email}.")
        return redirect("control_room:team_user", pk=pk)


class TeamRevokeInviteView(TeamManagementMixin, View):
    def post(self, request, pk):
        invitation = get_object_or_404(StaffInvitation, pk=pk)
        if revoke_invitation(invitation):
            messages.success(request, f"Revoked invitation for {invitation.email}.")
        else:
            messages.warning(request, "Invitation could not be revoked.")
        return redirect("control_room:team")
