"""TOTP MFA helpers."""

from __future__ import annotations

import hashlib
import secrets

import pyotp
from django.conf import settings

from accounts.models import AuditEventType, MFAMethod
from accounts.services.audit import log_audit_event
from accounts.services.email import get_or_create_security_profile


def generate_totp_secret() -> str:
    return pyotp.random_base32()


def provisioning_uri(user, secret: str) -> str:
    issuer = getattr(settings, "SITE_NAME", "Enterprise Platform")
    return pyotp.TOTP(secret).provisioning_uri(name=user.email, issuer_name=issuer)


def verify_totp(secret: str, code: str) -> bool:
    if not secret or not code:
        return False
    cleaned = str(code).strip().replace(" ", "")
    return pyotp.TOTP(secret).verify(cleaned, valid_window=1)


def generate_backup_codes(count: int = 8) -> tuple[list[str], list[str]]:
    plain = [f"{secrets.token_hex(2).upper()}-{secrets.token_hex(2).upper()}" for _ in range(count)]
    hashed = [_hash_backup_code(code) for code in plain]
    return plain, hashed


def _hash_backup_code(code: str) -> str:
    return hashlib.sha256(code.strip().upper().encode()).hexdigest()


def verify_backup_code(profile, code: str) -> bool:
    if not code or not profile.backup_codes:
        return False
    digest = _hash_backup_code(code)
    if digest not in profile.backup_codes:
        return False
    profile.backup_codes = [item for item in profile.backup_codes if item != digest]
    profile.save(update_fields=["backup_codes", "updated_at"])
    return True


def enable_totp(user, secret: str, backup_hashes: list[str], *, request=None):
    profile = get_or_create_security_profile(user)
    profile.mfa_enabled = True
    profile.mfa_method = MFAMethod.TOTP
    profile.mfa_secret = secret
    profile.backup_codes = backup_hashes
    profile.save(update_fields=["mfa_enabled", "mfa_method", "mfa_secret", "backup_codes", "updated_at"])
    log_audit_event(AuditEventType.MFA_ENABLED, request=request, user=user, message="TOTP MFA enabled")


def disable_mfa(user, *, request=None):
    profile = get_or_create_security_profile(user)
    profile.mfa_enabled = False
    profile.mfa_method = MFAMethod.NONE
    profile.mfa_secret = ""
    profile.backup_codes = []
    profile.save(
        update_fields=["mfa_enabled", "mfa_method", "mfa_secret", "backup_codes", "updated_at"]
    )
    log_audit_event(AuditEventType.MFA_DISABLED, request=request, user=user, message="MFA disabled")


def verify_mfa_code(profile, code: str) -> bool:
    if profile.mfa_method == MFAMethod.TOTP and verify_totp(profile.mfa_secret, code):
        return True
    return verify_backup_code(profile, code)
