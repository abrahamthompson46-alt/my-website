import logging

from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.cache import cache_page, never_cache
from django.views.decorators.http import require_GET

logger = logging.getLogger(__name__)


@cache_page(60 * 60 * 24)
def robots_txt(request):
    content = render_to_string("robots.txt", request=request)
    return HttpResponse(content, content_type="text/plain")


@never_cache
@require_GET
def health_check(request):
    """Public readiness probe for load balancers and orchestrators."""
    checks = {}
    degraded = False

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks["database"] = "ok"
    except Exception:
        logger.exception("Health check: database unavailable")
        checks["database"] = "unavailable"
        return JsonResponse({"status": "error", "checks": checks}, status=503)

    try:
        from django.core.cache import cache

        from common.cache_utils import get_cache_backend_label

        cache.set("health_probe", "ok", 5)
        cache_value = cache.get("health_probe")
        if cache_value == "ok":
            checks["cache"] = "ok"
        else:
            checks["cache"] = "degraded"
            degraded = True
        checks["cache_backend"] = get_cache_backend_label()
    except Exception:
        logger.exception("Health check: cache unavailable")
        checks["cache"] = "degraded"
        degraded = True

    overall = "degraded" if degraded else "ok"
    status_code = 200 if overall != "error" else 503
    return JsonResponse({"status": overall, "checks": checks}, status=status_code)
