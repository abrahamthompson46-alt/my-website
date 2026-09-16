"""Mark non-live catalog products as coming soon; tighten CoreTrust outbound URLs."""

from django.db import migrations


LIVE_PRODUCT_LINKS = {
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
        "demo_url": "https://micro.zreta.com/request-demo/",
        "register_url": "https://micro.zreta.com/request-demo/",
        "external_app_url": "https://micro.zreta.com/",
        "is_featured": True,
        "is_published": True,
        "status": "ga",
    },
}

COMING_SOON_SLUGS = (
    "erp-suite",
    "school-management",
    "hospital-management",
    "hr-payroll",
    "retail-commerce",
)


def align_catalog_honesty(apps, schema_editor):
    Product = apps.get_model("products", "Product")

    for slug, fields in LIVE_PRODUCT_LINKS.items():
        Product.objects.filter(slug=slug).update(**fields)

    Product.objects.filter(slug__in=COMING_SOON_SLUGS).update(
        status="coming_soon",
        is_featured=False,
    )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0005_align_live_product_outbound_urls"),
    ]

    operations = [
        migrations.RunPython(align_catalog_honesty, noop_reverse),
    ]
