"""JWT helper utilities."""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jose import JWTError, jwt

from app.config import settings


def _create_token(subject: str, expires_delta: timedelta, extra: Optional[Dict[str, Any]] = None) -> str:
    payload: Dict[str, Any] = extra.copy() if extra else {}
    expire = datetime.now(timezone.utc) + expires_delta
    payload.update({"exp": expire, "sub": subject, "iat": datetime.now(timezone.utc)})
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(subject: str, extra: Optional[Dict[str, Any]] = None) -> str:
    """Create a signed access token."""
    expiry = timedelta(seconds=settings.access_token_expire_seconds)
    return _create_token(subject, expiry, extra)


def create_refresh_token(subject: str, extra: Optional[Dict[str, Any]] = None) -> str:
    """Create a signed refresh token."""
    expiry = timedelta(days=settings.refresh_token_expire_days)
    return _create_token(subject, expiry, extra)


def verify_access_token(token: str) -> Dict[str, Any]:
    """Decode and verify an access token."""
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


def decode_refresh_token(token: str) -> Dict[str, Any]:
    """Decode refresh token (same secret)."""
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


class TokenError(Exception):
    """Wrapper for token errors."""

    def __init__(self, message: str = "Invalid token", original: Optional[JWTError] = None) -> None:
        super().__init__(message)
        self.original = original
