"""Reposition Microfinance Core as external CoreTrust; drop in-repo MFI tables."""

from django.db import migrations


CORETRUST_COPY = {
    "name": "CoreTrust",
    "tagline": "Core banking for microfinance institutions",
    "short_description": (
        "Live MFI platform for loans, savings, collections, and operations — "
        "marketed and billed through Zreta, running as its own product."
    ),
    "long_description": (
        "CoreTrust is Zreta's microfinance product. It is a separate, deployed application "
        "for MFIs, SACCOs, and cooperatives. This website markets CoreTrust, sells "
        "subscriptions, and links customers to the live app — it does not host the "
        "banking engine itself."
    ),
    "external_app_url": "https://micro.zreta.com/",
    "demo_url": "https://micro.zreta.com/",
    "register_url": "https://micro.zreta.com/",
    "is_featured": True,
    "status": "ga",
    "is_published": True,
}


def align_coretrust(apps, schema_editor):
    Product = apps.get_model("products", "Product")
    Product.objects.filter(slug="microfinance-core").update(**CORETRUST_COPY)


def drop_legacy_mfi_tables(apps, schema_editor):
    """Remove experimental in-repo MFI tables if a prior Phase 3 migration applied them."""
    statements = [
        "DROP TABLE IF EXISTS ledger_journalline",
        "DROP TABLE IF EXISTS ledger_journalentry",
        "DROP TABLE IF EXISTS ledger_account",
        "DROP TABLE IF EXISTS ledger_businessday",
        "DROP TABLE IF EXISTS ledger_businesscalendar",
        "DROP TABLE IF EXISTS clients_client",
        "DELETE FROM django_migrations WHERE app IN ('ledger', 'clients')",
    ]
    with schema_editor.connection.cursor() as cursor:
        for sql in statements:
            cursor.execute(sql)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0003_churchhub_external_links"),
    ]

    operations = [
        migrations.RunPython(align_coretrust, noop_reverse),
        migrations.RunPython(drop_legacy_mfi_tables, noop_reverse),
    ]
