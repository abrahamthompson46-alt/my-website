"""Set ChurchHub external demo and registration URLs."""

from django.db import migrations


def forwards(apps, schema_editor):
    Product = apps.get_model("products", "Product")
    Product.objects.filter(slug="churchhub").update(
        demo_url="https://mychurch.zreta.com/contact/",
        register_url="https://mychurch.zreta.com/apply/",
        external_app_url="https://mychurch.zreta.com/",
    )


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0002_product_external_links_and_media_kinds"),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
