"""User models and schemas for authentication."""
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from enum import Enum


class UserRole(str, Enum):
    """User roles for RBAC."""
    ADMIN = "admin"  # Full access, can enable live trading
    OPERATOR = "operator"  # Can pause/resume, view all data
    VIEWER = "viewer"  # Read-only access


class User(BaseModel):
    """User model."""
    id: str
    email: EmailStr
    username: str
    hashed_password: str
    role: UserRole = UserRole.VIEWER
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None
    api_key: Optional[str] = None  # For programmatic access


class UserCreate(BaseModel):
    """Schema for creating a new user."""
    email: EmailStr
    username: str
    password: str
    role: UserRole = UserRole.VIEWER


class UserLogin(BaseModel):
    """Schema for user login."""
    username: str
    password: str


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    refresh_token: Optional[str] = None


class TokenData(BaseModel):
    """Data encoded in JWT token."""
    username: str
    role: UserRole
    exp: datetime


class UserResponse(BaseModel):
    """Public user information."""
    id: str
    email: EmailStr
    username: str
    role: UserRole
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]


class APIKeyCreate(BaseModel):
    """Schema for creating API key."""
    name: str
    expires_in_days: int = 90


class APIKeyResponse(BaseModel):
    """API key response (shown only once)."""
    api_key: str
    name: str
    expires_at: datetime
