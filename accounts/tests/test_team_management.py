from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import Role, StaffInvitation
from accounts.services.invitations import accept_invitation, create_staff_invitation, get_invitation_by_token
from accounts.services.email import get_or_create_security_profile
from accounts.services.rbac import assign_role, remove_role, sync_user_permissions, user_can_manage_team

User = get_user_model()


class RBACPermissionSyncTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="rbacuser", email="rbac@example.com", password="pass")
        self.role_a = Role.objects.create(name="Role A", slug="role-a")
        self.role_b = Role.objects.create(name="Role B", slug="role-b")
        perm = Permission.objects.filter(codename="view_user").first()
        if perm:
            self.role_a.permissions.add(perm)
            self.role_b.permissions.add(perm)

    def test_remove_role_keeps_shared_permissions(self):
        assign_role(self.user, self.role_a)
        assign_role(self.user, self.role_b)
        self.assertTrue(self.user.has_perm("accounts.view_user"))
        remove_role(self.user, self.role_a)
        self.assertTrue(self.user.has_perm("accounts.view_user"))

    def test_sync_user_permissions_rebuilds_from_roles(self):
        assign_role(self.user, self.role_a)
        self.user.user_permissions.clear()
        sync_user_permissions(self.user)
        if self.role_a.permissions.exists():
            self.assertTrue(self.user.has_perm("accounts.view_user"))


class TeamManagementAccessTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner", email="owner@example.com", password="pass", is_staff=True
        )
        self.staff = User.objects.create_user(
            username="staff", email="staff@example.com", password="pass", is_staff=True
        )
        self.owner_role = Role.objects.create(name="Platform Owner", slug="platform-owner")
        self.support_role = Role.objects.create(name="Support Agent", slug="support-agent")
        assign_role(self.owner, self.owner_role)
        for user in (self.owner, self.staff):
            profile = get_or_create_security_profile(user)
            profile.mark_email_verified()
            profile.mfa_enabled = True
            profile.save(update_fields=["email_verified", "email_verified_at", "mfa_enabled", "updated_at"])

    def test_owner_can_access_team_page(self):
        self.assertTrue(user_can_manage_team(self.owner))
        self.client.login(username="owner@example.com", password="pass")
        response = self.client.get(reverse("control_room:team"))
        self.assertEqual(response.status_code, 200)

    def test_plain_staff_cannot_access_team_page(self):
        self.assertFalse(user_can_manage_team(self.staff))
        self.client.login(username="staff@example.com", password="pass")
        response = self.client.get(reverse("control_room:team"))
        self.assertEqual(response.status_code, 403)


class StaffInvitationTests(TestCase):
    def setUp(self):
        self.inviter = User.objects.create_user(
            username="inviter", email="inviter@example.com", password="pass", is_staff=True
        )
        self.role = Role.objects.create(name="Platform Admin", slug="platform-admin")

    def test_accept_invitation_creates_staff_user(self):
        invitation, raw = create_staff_invitation(
            email="newadmin@example.com",
            role=self.role,
            invited_by=self.inviter,
            grant_staff_access=True,
        )
        user = User.objects.create_user(username="newadmin", email="newadmin@example.com", password="pass")
        accept_invitation(invitation, user=user)
        user.refresh_from_db()
        invitation.refresh_from_db()
        self.assertTrue(user.is_staff)
        self.assertEqual(invitation.status, "accepted")
        self.assertTrue(user.user_roles.filter(role=self.role).exists())

    def test_invitation_expires_in_one_hour(self):
        invitation, _ = create_staff_invitation(
            email="timed@example.com",
            role=self.role,
            invited_by=self.inviter,
        )
        delta = invitation.expires_at - invitation.created_at
        self.assertGreater(delta.total_seconds(), 3500)
        self.assertLessEqual(delta.total_seconds(), 3600)

    def test_invitation_link_is_one_time_use(self):
        invitation, raw = create_staff_invitation(
            email="once@example.com",
            role=self.role,
            invited_by=self.inviter,
        )
        user = User.objects.create_user(username="once", email="once@example.com", password="pass")
        accept_invitation(invitation, user=user)

        self.assertIsNone(get_invitation_by_token(raw))
        response = self.client.get(reverse("accounts:accept_invite", kwargs={"token": raw}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "invalid or has already been used")

    def test_accept_invite_page_loads(self):
        invitation, raw = create_staff_invitation(
            email="invite@example.com",
            role=self.role,
            invited_by=self.inviter,
        )
        response = self.client.get(reverse("accounts:accept_invite", kwargs={"token": raw}))
        self.assertEqual(response.status_code, 200)
