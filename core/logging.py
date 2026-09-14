"""Structured logging helpers."""

from __future__ import annotations

import json
import logging
from contextvars import ContextVar
from datetime import datetime, timezone

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")

logger = logging.getLogger(__name__)


class RequestIDFilter(logging.Filter):
    """Inject request_id from contextvars into every log record."""

    def filter(self, record):
        record.request_id = request_id_var.get()
        return True


class JsonFormatter(logging.Formatter):
    """Emit one JSON object per log line for log shippers."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
            "module": record.module,
            "process": record.process,
            "thread": record.thread,
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        if record.stack_info:
            payload["stack_info"] = self.formatStack(record.stack_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def get_request_id(request=None) -> str | None:
    if request is not None:
        return getattr(request, "request_id", None)
    value = request_id_var.get()
    return None if value == "-" else value


def set_request_id(request_id: str):
    return request_id_var.set(request_id)


def reset_request_id(token) -> None:
    request_id_var.reset(token)
