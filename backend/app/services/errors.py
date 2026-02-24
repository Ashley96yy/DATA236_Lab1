"""
Service-layer exceptions.

Endpoints catch these and translate them to HTTPException with the
appropriate HTTP status code.

Mapping:
    ServiceNotFound      → 404
    ServiceUnauthorized  → 401
    ServiceForbidden     → 403
    ServiceConflict      → 409
    ServiceBadRequest    → 400
"""
from __future__ import annotations


class ServiceNotFound(Exception):
    """Raised when a requested resource does not exist."""


class ServiceUnauthorized(Exception):
    """Raised when the caller's identity cannot be verified (token invalid/absent)."""


class ServiceForbidden(Exception):
    """Raised when the caller is authenticated but lacks permission."""


class ServiceConflict(Exception):
    """Raised when an action violates a uniqueness / state constraint."""


class ServiceBadRequest(Exception):
    """Raised when input fails a business-rule validation."""
