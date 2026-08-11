"""Add Documentation link to Control Room sidebar navigation."""

from django.db import migrations


def forwards(apps, schema_editor):
    from common import navigation as nav_constants

    NavigationMenu = apps.get_model("control_room", "NavigationMenu")
    NavigationMenu.objects.filter(code="control_room").update(
        structure=nav_constants.CONTROL_ROOM_NAV
    )


class Migration(migrations.Migration):
    dependencies = [
        ("control_room", "0008_brand_file_uploads"),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
