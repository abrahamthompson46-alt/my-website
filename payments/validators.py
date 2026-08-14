"""Validators for payment proof uploads."""

from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

MAX_PROOF_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

PROOF_FILE_EXTENSIONS = ["pdf", "png", "jpg", "jpeg", "webp"]

validate_proof_file_extension = FileExtensionValidator(
    allowed_extensions=PROOF_FILE_EXTENSIONS,
    message="Upload a PDF, PNG, JPG, or WEBP file.",
)


def validate_proof_file_size(value) -> None:
    if value and value.size > MAX_PROOF_FILE_SIZE:
        raise ValidationError("Proof file must be 5 MB or smaller.")
