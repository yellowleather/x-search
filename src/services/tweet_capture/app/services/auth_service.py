"""Authentication business logic."""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict
from uuid import uuid4

from fastapi import HTTPException, status

from app.config import settings
from app.services.firestore_service import FirestoreService
from app.utils.jwt import create_access_token, create_refresh_token, decode_refresh_token
from app.utils.password import hash_password, verify_password


class AuthService:
    """Service for registration, login, and refresh."""

    def __init__(self, firestore: FirestoreService) -> None:
        self.firestore = firestore

    async def register(self, email: str, password: str) -> Dict[str, Any]:
        existing = await self.firestore.get_user_by_email(email)
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

        user_id = str(uuid4())
        password_hash = hash_password(password)
        await self.firestore.create_user(
            user_id,
            {
                "email": email,
                "passwordHash": password_hash,
                "isActive": True,
                "createdAt": datetime.now(timezone.utc),
                "updatedAt": datetime.now(timezone.utc),
            },
        )
        return await self._issue_tokens(user_id, email)

    async def login(self, email: str, password: str) -> Dict[str, Any]:
        user = await self.firestore.get_user_by_email(email)
        if not user or not verify_password(password, user["passwordHash"]):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        if not user.get("isActive", True):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")
        return await self._issue_tokens(user["id"], email)

    async def refresh(self, refresh_token: str) -> Dict[str, Any]:
        session = await self.firestore.get_session_by_refresh_token(refresh_token)
        if not session:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
        try:
            payload = decode_refresh_token(refresh_token)
        except Exception as exc:  # pylint: disable=broad-except
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc
        user_id = payload.get("sub")
        email = payload.get("email")
        if not user_id or not email:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
        access_token = create_access_token(user_id, {"email": email})
        return {
            "accessToken": access_token,
            "expiresIn": settings.access_token_expire_seconds,
            "tokenType": "Bearer",
        }

    async def _issue_tokens(self, user_id: str, email: str) -> Dict[str, Any]:
        access_token = create_access_token(user_id, {"email": email})
        refresh_token = create_refresh_token(user_id, {"email": email})
        session_id = str(uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
        await self.firestore.create_session(
            session_id,
            {
                "userId": user_id,
                "refreshToken": refresh_token,
                "expiresAt": expires_at,
                "createdAt": datetime.now(timezone.utc),
                "lastUsedAt": datetime.now(timezone.utc),
            },
        )
        return {
            "userId": user_id,
            "email": email,
            "accessToken": access_token,
            "refreshToken": refresh_token,
            "expiresIn": settings.access_token_expire_seconds,
            "tokenType": "Bearer",
        }
