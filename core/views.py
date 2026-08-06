from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.cache import cache_page, never_cache
from django.views.decorators.http import require_GET


@cache_page(60 * 60 * 24)
def robots_txt(request):
    content = render_to_string("robots.txt", request=request)
    return HttpResponse(content, content_type="text/plain")


@never_cache
@require_GET
def health_check(request):
    """Public readiness probe for load balancers and orchestrators."""
    checks = {}

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks["database"] = "ok"
    except Exception as exc:
        return JsonResponse(
            {"status": "error", "checks": {"database": str(exc)}},
            status=503,
        )

    try:
        from django.core.cache import cache

        from common.cache_utils import get_cache_backend_label

        cache.set("health_probe", "ok", 5)
        checks["cache"] = "ok" if cache.get("health_probe") == "ok" else "degraded"
        checks["cache_backend"] = get_cache_backend_label()
    except Exception as exc:
        checks["cache"] = str(exc)

    overall = "ok" if checks.get("database") == "ok" else "error"
    status_code = 200 if overall == "ok" else 503
    return JsonResponse({"status": overall, "checks": checks}, status=status_code)