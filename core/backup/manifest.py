"""Backup foundation helpers — path safety and manifest validation."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

BACKUP_ROOT_DEFAULT = Path("/var/backups/zreta")

# Paths that must never be used as backup storage (web-exposed).
FORBIDDEN_BACKUP_PREFIXES = (
    "/media/",
    "media/",
    "/static/",
    "static/",
    "/var/www/marketing-site/media/",
)

SECRET_FILENAME_PATTERN = re.compile(
    r"(password|secret|credential|\.env|private.?key|id_rsa)",
    re.IGNORECASE,
)

PG_IDENTIFIER_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]{0,62}$")


@dataclass(frozen=True)
class BackupManifest:
    schema_version: int
    backup_type: str
    created_at_utc: str
    hostname: str
    app_dir: str
    database_name: str
    artifact: str
    size_bytes: int
    sha256: str

    @classmethod
    def from_dict(cls, data: dict) -> BackupManifest:
        return cls(
            schema_version=int(data["schema_version"]),
            backup_type=str(data["backup_type"]),
            created_at_utc=str(data["created_at_utc"]),
            hostname=str(data.get("hostname", "")),
            app_dir=str(data.get("app_dir", "")),
            database_name=str(data.get("database_name", "")),
            artifact=str(data["artifact"]),
            size_bytes=int(data["size_bytes"]),
            sha256=str(data["sha256"]),
        )


def normalize_path(path: str | Path) -> str:
    return str(path).replace("\\", "/").rstrip("/")


def is_safe_backup_root(path: str | Path) -> bool:
    """Return True when a backup root is not under public web-served directories."""
    normalized = normalize_path(path).lower()
    if not normalized:
        return False
    return not any(normalized.startswith(prefix) for prefix in FORBIDDEN_BACKUP_PREFIXES)


def is_safe_backup_filename(name: str) -> bool:
    """Reject filenames that may embed secrets or env files."""
    if not name or name != Path(name).name:
        return False
    if SECRET_FILENAME_PATTERN.search(name):
        return False
    return True


def normalize_pg_identifier(name: str) -> str:
    """Normalize a PostgreSQL identifier the way unquoted names are stored."""
    return name.lower()


def is_safe_pg_identifier(name: str) -> bool:
    """Return True when name is a valid unquoted PostgreSQL identifier."""
    return bool(name and PG_IDENTIFIER_PATTERN.match(name))


def is_production_db_name(target: str, production: str) -> bool:
    """Case-insensitive production database name match."""
    return normalize_pg_identifier(target) == normalize_pg_identifier(production)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(path: Path) -> BackupManifest:
    data = json.loads(path.read_text(encoding="utf-8"))
    return BackupManifest.from_dict(data)


def verify_manifest_artifact(manifest_path: Path) -> tuple[bool, str]:
    """Verify manifest checksum and artifact size. Returns (ok, message)."""
    manifest = load_manifest(manifest_path)
    if not is_safe_backup_filename(manifest.artifact):
        return False, f"Unsafe artifact filename: {manifest.artifact}"

    artifact = manifest_path.parent / manifest.artifact
    if not artifact.is_file():
        return False, f"Artifact missing: {artifact}"

    size = artifact.stat().st_size
    if size != manifest.size_bytes:
        return False, f"Size mismatch: expected {manifest.size_bytes}, got {size}"

    actual = sha256_file(artifact)
    if actual != manifest.sha256:
        return False, "SHA-256 checksum mismatch"

    return True, "manifest verified"
