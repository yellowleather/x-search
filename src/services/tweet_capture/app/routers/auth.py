"""Authentication routes."""
from fastapi import APIRouter

from app.config import settings
from app.models.auth import LoginRequest, RefreshRequest, RefreshResponse, RegisterRequest, TokenResponse
from app.services.auth_service import AuthService
from app.services.firestore_service import FirestoreService

router = APIRouter()

firestore_service = FirestoreService(settings.gcp_project_id, settings.firestore_database)
auth_service = AuthService(firestore_service)


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(payload: RegisterRequest) -> TokenResponse:
    """Register a new user."""
    result = await auth_service.register(payload.email, payload.password)
    return TokenResponse(**result)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest) -> TokenResponse:
    """Login existing user."""
    result = await auth_service.login(payload.email, payload.password)
    return TokenResponse(**result)


@router.post("/refresh", response_model=RefreshResponse)
async def refresh(payload: RefreshRequest) -> RefreshResponse:
    """Refresh access token."""
    result = await auth_service.refresh(payload.refreshToken)
    return RefreshResponse(**result)
