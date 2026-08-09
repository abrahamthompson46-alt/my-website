"""Sync public nav menus so product links go to product detail pages."""

from django.db import migrations


def forwards(apps, schema_editor):
    from common import navigation as nav_constants

    NavigationMenu = apps.get_model("control_room", "NavigationMenu")
    updates = {
        "public_header": nav_constants.PUBLIC_HEADER_NAV,
        "public_footer": nav_constants.PUBLIC_FOOTER_COLUMNS,
    }
    for code, structure in updates.items():
        NavigationMenu.objects.filter(code=code).update(structure=structure)


class Migration(migrations.Migration):
    dependencies = [
        ("control_room", "0003_update_header_cta_urls"),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
