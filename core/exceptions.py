from django.core.exceptions import PermissionDenied
from django.http import Http404


class AppException(Exception):
    """Base exception for application errors."""

    default_message = "An unexpected error occurred."

    def __init__(self, message=None):
        self.message = message or self.default_message
        super().__init__(self.message)


class NotFoundError(AppException):
    default_message = "Resource not found."

    def to_http404(self):
        return Http404(self.message)


class PermissionError(AppException):
    default_message = "Permission denied."

    def to_permission_denied(self):
        return PermissionDenied(self.message)
