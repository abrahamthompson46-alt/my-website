"""Media path helpers — separate public marketing assets from private uploads."""

from __future__ import annotations

PRIVATE_MEDIA_PREFIX = "private/"
LEGACY_PRIVATE_PREFIXES = (
    "payments/proofs/",
)


def normalize_media_relative_path(path: str) -> str:
    return path.replace("\\", "/").lstrip("/")


def is_private_media_path(path: str) -> bool:
    """Return True when a relative media path must not be served publicly."""
    normalized = normalize_media_relative_path(path)
    if normalized.startswith(PRIVATE_MEDIA_PREFIX):
        return True
    return any(normalized.startswith(prefix) for prefix in LEGACY_PRIVATE_PREFIXES)


def private_payment_proof_upload_to(instance, filename: str) -> str:
    """Store payment proofs under the private media prefix."""
    safe_name = filename.rsplit("/", 1)[-1]
    return f"{PRIVATE_MEDIA_PREFIX}payments/proofs/{safe_name}"
