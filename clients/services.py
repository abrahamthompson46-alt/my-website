"""Services for org-scoped MFI client / borrower management."""

from __future__ import annotations

from datetime import date

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from clients.exceptions import (
    ClientError,
    ClientNotFoundError,
    DuplicateClientError,
    InvalidClientStatusError,
)
from clients.models import Client, ClientStatus, ClientType


def clients_for_organization(organization, *, status: str | None = None):
    """Tenant-scoped client queryset."""
    qs = Client.objects.filter(organization=organization)
    if status is not None:
        qs = qs.filter(status=status)
    return qs


def get_client_for_organization(organization, client_id) -> Client:
    """Fetch a client by id ensuring it belongs to the organization."""
    try:
        return Client.objects.get(organization=organization, pk=client_id)
    except Client.DoesNotExist as exc:
        raise ClientNotFoundError("Client not found for this organization.") from exc


def next_client_number(organization) -> str:
    """
    Allocate the next ``CL-000001`` style number for the organization.

    Uses the max existing numeric suffix; gaps are not reused.
    """
    existing = (
        Client.objects.filter(organization=organization, client_number__startswith="CL-")
        .order_by("-client_number")
        .values_list("client_number", flat=True)
    )
    max_n = 0
    for number in existing:
        suffix = number.split("-", 1)[-1]
        if suffix.isdigit():
            max_n = max(max_n, int(suffix))
    return f"CL-{max_n + 1:06d}"


def _resolve_display_name(
    *,
    display_name: str,
    first_name: str,
    last_name: str,
    other_names: str,
    client_type: str,
) -> str:
    if display_name and display_name.strip():
        return display_name.strip()
    if client_type == ClientType.INDIVIDUAL:
        parts = [first_name, other_names, last_name]
        assembled = " ".join(p.strip() for p in parts if p and p.strip())
        if assembled:
            return assembled
    raise ClientError("display_name is required (or first/last name for individuals).")


def _is_duplicate_validation(exc: ValidationError) -> bool:
    messages = []
    if hasattr(exc, "message_dict"):
        for key, vals in exc.message_dict.items():
            if key in {"client_number", "national_id", "__all__"}:
                messages.extend(str(v) for v in vals)
    else:
        messages.extend(str(v) for v in exc.messages)
    blob = " ".join(messages).lower()
    return any(
        token in blob
        for token in (
            "already exists",
            "uniq_mfi_client_org_number",
            "uniq_mfi_client_org_national_id",
            "client number",
            "national id",
        )
    )


@transaction.atomic
def create_client(
    *,
    organization,
    client_type: str = ClientType.INDIVIDUAL,
    display_name: str = "",
    first_name: str = "",
    last_name: str = "",
    other_names: str = "",
    phone: str = "",
    email: str = "",
    national_id: str = "",
    date_of_birth: date | None = None,
    address_line1: str = "",
    address_line2: str = "",
    city: str = "",
    region: str = "",
    country: str = "GH",
    notes: str = "",
    external_reference: str = "",
    client_number: str | None = None,
    status: str = ClientStatus.ACTIVE,
    created_by=None,
) -> Client:
    """Create a borrower/client record for an organization."""
    if client_type not in ClientType.values:
        raise ClientError(f"Unknown client type: {client_type}")
    if status not in ClientStatus.values:
        raise InvalidClientStatusError(f"Unknown client status: {status}")

    resolved_name = _resolve_display_name(
        display_name=display_name,
        first_name=first_name,
        last_name=last_name,
        other_names=other_names,
        client_type=client_type,
    )
    number = (client_number or next_client_number(organization)).strip().upper()

    client = Client(
        organization=organization,
        client_number=number,
        client_type=client_type,
        status=status,
        display_name=resolved_name,
        first_name=(first_name or "").strip(),
        last_name=(last_name or "").strip(),
        other_names=(other_names or "").strip(),
        phone=(phone or "").strip(),
        email=(email or "").strip(),
        national_id=(national_id or "").strip(),
        date_of_birth=date_of_birth,
        address_line1=(address_line1 or "").strip(),
        address_line2=(address_line2 or "").strip(),
        city=(city or "").strip(),
        region=(region or "").strip(),
        country=(country or "GH").strip().upper()[:2] or "GH",
        notes=notes or "",
        external_reference=(external_reference or "").strip(),
        created_by=created_by,
    )
    try:
        client.full_clean()
        client.save()
    except ValidationError as exc:
        if _is_duplicate_validation(exc):
            raise DuplicateClientError(str(exc)) from exc
        raise ClientError(str(exc)) from exc
    except IntegrityError as exc:
        raise DuplicateClientError("Client number or national ID already exists.") from exc
    return client


@transaction.atomic
def update_client(
    client: Client,
    *,
    organization=None,
    **fields,
) -> Client:
    """
    Update mutable client profile fields.

    When ``organization`` is provided, enforces tenant match.
    """
    if organization is not None and client.organization_id != organization.id:
        raise ClientNotFoundError("Client not found for this organization.")

    allowed = {
        "display_name",
        "first_name",
        "last_name",
        "other_names",
        "phone",
        "email",
        "national_id",
        "date_of_birth",
        "address_line1",
        "address_line2",
        "city",
        "region",
        "country",
        "notes",
        "external_reference",
        "client_type",
    }
    for key, value in fields.items():
        if key not in allowed:
            raise ClientError(f"Field cannot be updated via update_client: {key}")
        if key == "client_type" and value not in ClientType.values:
            raise ClientError(f"Unknown client type: {value}")
        if isinstance(value, str) and key not in {"notes"}:
            value = value.strip()
        setattr(client, key, value)

    try:
        client.full_clean()
        client.save()
    except ValidationError as exc:
        if _is_duplicate_validation(exc):
            raise DuplicateClientError(str(exc)) from exc
        raise ClientError(str(exc)) from exc
    except IntegrityError as exc:
        raise DuplicateClientError("National ID already exists for this organization.") from exc
    return client


def set_client_status(client: Client, status: str, *, organization=None) -> Client:
    """Change client status with optional tenant check."""
    if organization is not None and client.organization_id != organization.id:
        raise ClientNotFoundError("Client not found for this organization.")
    if status not in ClientStatus.values:
        raise InvalidClientStatusError(f"Unknown client status: {status}")
    if client.status == ClientStatus.CLOSED and status != ClientStatus.CLOSED:
        raise InvalidClientStatusError("Closed clients cannot be reopened in this slice.")
    client.status = status
    client.save(update_fields=["status", "updated_at"])
    return client


def deactivate_client(client: Client, *, organization=None) -> Client:
    """Mark a client inactive (soft offboarding)."""
    return set_client_status(client, ClientStatus.INACTIVE, organization=organization)
