"""Align live product outbound demo/register URLs for homepage CTAs."""

from django.db import migrations


PRODUCT_LINKS = {
    "churchhub": {
        "demo_url": "https://mychurch.zreta.com/contact/",
        "register_url": "https://mychurch.zreta.com/apply/",
        "external_app_url": "https://mychurch.zreta.com/",
        "is_featured": True,
        "is_published": True,
        "status": "ga",
    },
    "microfinance-core": {
        "name": "CoreTrust",
        "demo_url": "https://micro.zreta.com/",
        "register_url": "https://micro.zreta.com/",
        "external_app_url": "https://micro.zreta.com/",
        "is_featured": True,
        "is_published": True,
        "status": "ga",
    },
}


def align_product_links(apps, schema_editor):
    Product = apps.get_model("products", "Product")
    for slug, fields in PRODUCT_LINKS.items():
        Product.objects.filter(slug=slug).update(**fields)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0004_coretrust_external_product"),
    ]

    operations = [
        migrations.RunPython(align_product_links, noop_reverse),
    ]
