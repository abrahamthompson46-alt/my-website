"""Client / borrower domain errors."""


class ClientError(Exception):
    """Base error for client operations."""


class ClientNotFoundError(ClientError):
    """Client does not exist in the requested organization."""


class DuplicateClientError(ClientError):
    """Client number or national ID already exists for the organization."""


class InvalidClientStatusError(ClientError):
    """Requested status transition is not allowed."""
