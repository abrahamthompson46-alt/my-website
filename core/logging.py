import logging
import uuid

logger = logging.getLogger(__name__)


class RequestIDFilter(logging.Filter):
    """Inject request_id into log records when available."""

    def filter(self, record):
        if not hasattr(record, "request_id"):
            record.request_id = "-"
        return True


def get_request_id(request):
    return getattr(request, "request_id", None)
