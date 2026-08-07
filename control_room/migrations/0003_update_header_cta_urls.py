"""Update header CTA URL names to dedicated contact routes."""

from django.db import migrations


def forwards(apps, schema_editor):
    PlatformSettings = apps.get_model("control_room", "PlatformSettings")
    PlatformSettings.objects.filter(header_cta_primary_url_name="contact:form").update(
        header_cta_primary_url_name="contact:trial"
    )
    PlatformSettings.objects.filter(header_cta_secondary_url_name="contact:form").update(
        header_cta_secondary_url_name="contact:demo"
    )


class Migration(migrations.Migration):
    dependencies = [
        ("control_room", "0002_brand_colors"),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
