"""Validators for platform branding uploads."""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

MAX_BRAND_FILE_SIZE = 2 * 1024 * 1024  # 2 MB

BRAND_FILE_EXTENSIONS = ["png", "jpg", "jpeg", "gif", "webp", "svg", "ico"]

validate_brand_file_extension = FileExtensionValidator(
    allowed_extensions=BRAND_FILE_EXTENSIONS,
    message="Upload a PNG, JPG, WEBP, SVG, or ICO file.",
)


def validate_brand_file_size(value) -> None:
    if value and value.size > MAX_BRAND_FILE_SIZE:
        raise ValidationError("File must be 2 MB or smaller.")


def favicon_mime_type(url: str) -> str:
    """Return the MIME type for a favicon URL based on its extension."""
    lowered = (url or "").lower().split("?", 1)[0]
    if lowered.endswith(".svg"):
        return "image/svg+xml"
    if lowered.endswith(".ico"):
        return "image/x-icon"
    if lowered.endswith(".png"):
        return "image/png"
    if lowered.endswith(".webp"):
        return "image/webp"
    if lowered.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    if lowered.endswith(".gif"):
        return "image/gif"
    return "image/png"
