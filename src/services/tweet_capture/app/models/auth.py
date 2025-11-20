"""Pydantic models for authentication endpoints."""
from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    userId: str
    email: EmailStr
    accessToken: str
    refreshToken: str
    expiresIn: int
    tokenType: str = "Bearer"


class RefreshRequest(BaseModel):
    refreshToken: str = Field(..., min_length=10)


class RefreshResponse(BaseModel):
    accessToken: str
    expiresIn: int
    tokenType: str = "Bearer"
