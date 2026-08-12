"""Add Platform Ops nav link and grant permission to platform-owner role."""

from django.db import migrations


def forwards(apps, schema_editor):
    from common import navigation as nav_constants

    NavigationMenu = apps.get_model("control_room", "NavigationMenu")
    NavigationMenu.objects.filter(code="control_room").update(
        structure=nav_constants.CONTROL_ROOM_NAV
    )

    Role = apps.get_model("accounts", "Role")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")

    ct = ContentType.objects.filter(
        app_label="control_room",
        model="platformoperationssettings",
    ).first()
    if not ct:
        return

    perm = Permission.objects.filter(
        content_type=ct,
        codename="manage_platform_operations",
    ).first()
    if not perm:
        return

    role = Role.objects.filter(slug="platform-owner").first()
    if role:
        role.permissions.add(perm)


class Migration(migrations.Migration):
    dependencies = [
        ("control_room", "0010_platform_operations_settings"),
        ("accounts", "0003_team_and_branding"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
