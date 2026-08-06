import shutil
from pathlib import Path

from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.utils import timezone

from payments.models import Payment, PaymentStatus, WebhookEvent


def check_database():
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return {"status": "healthy", "message": "Database connected"}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


def check_cache():
    try:
        from common.cache_utils import get_cache_backend_label

        cache.set("ops_health_check", "ok", 10)
        ok = cache.get("ops_health_check") == "ok"
        backend = get_cache_backend_label()
        message = f"Cache operational ({backend})" if ok else "Cache read failed"
        return {"status": "healthy" if ok else "warning", "message": message, "backend": backend}
    except Exception as exc:
        return {"status": "warning", "message": f"Cache unavailable: {exc}"}


def check_disk():
    try:
        path = Path(getattr(settings, "BASE_DIR", "."))
        usage = shutil.disk_usage(path)
        free_gb = usage.free / (1024 ** 3)
        status = "healthy" if free_gb > 1 else "warning"
        return {"status": status, "message": f"{free_gb:.1f} GB free"}
    except Exception as exc:
        return {"status": "warning", "message": str(exc)}


def check_webhooks():
    unprocessed = WebhookEvent.objects.filter(processed=False).count()
    failed = WebhookEvent.objects.exclude(error_message="").count()
    status = "healthy" if unprocessed < 10 else "warning"
    return {
        "status": status,
        "message": f"{unprocessed} unprocessed, {failed} with errors",
        "unprocessed": unprocessed,
        "failed": failed,
    }


def check_payments_queue():
    pending = Payment.objects.filter(
        status__in=[PaymentStatus.PENDING_CONFIRMATION, PaymentStatus.PROCESSING]
    ).count()
    status = "healthy" if pending < 20 else "warning"
    return {"status": status, "message": f"{pending} payments awaiting action", "pending": pending}


def get_system_health():
    checks = {
        "database": check_database(),
        "cache": check_cache(),
        "disk": check_disk(),
        "webhooks": check_webhooks(),
        "payments": check_payments_queue(),
    }
    statuses = [c["status"] for c in checks.values()]
    if "error" in statuses:
        overall = "error"
    elif "warning" in statuses:
        overall = "warning"
    else:
        overall = "healthy"
    return {"overall": overall, "checks": checks, "checked_at": timezone.now()}
