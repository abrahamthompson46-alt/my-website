import uuid

from django.utils.cache import patch_response_headers


class RequestIDMiddleware:
    """Attach a unique request ID to each incoming request for tracing."""

    HEADER_NAME = "HTTP_X_REQUEST_ID"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.META.get(self.HEADER_NAME)
        if not request_id:
            request_id = str(uuid.uuid4())
        request.request_id = request_id

        response = self.get_response(request)
        response["X-Request-ID"] = request_id
        return response


class CacheControlMiddleware:
    """Apply Cache-Control headers for public HTML and static assets."""

    STATIC_PREFIXES = ("/static/", "/media/")
    CACHEABLE_PREFIXES = ("/", "/products/", "/marketing/", "/pages/", "/docs/", "/contact/", "/blog/")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.method != "GET" or response.status_code != 200:
            return response

        path = request.path
        if path.startswith(self.STATIC_PREFIXES):
            patch_response_headers(response, cache_timeout=60 * 60 * 24 * 30)
            return response

        if getattr(response, "streaming", False):
            return response

        content_type = response.get("Content-Type", "")
        user = getattr(request, "user", None)
        is_anonymous = user is None or not user.is_authenticated
        if "text/html" in content_type and is_anonymous:
            if path == "/" or path.startswith(self.CACHEABLE_PREFIXES):
                patch_response_headers(response, cache_timeout=300)
        return response
