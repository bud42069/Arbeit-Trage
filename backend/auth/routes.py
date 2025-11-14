"""Authentication API routes."""
import secrets
from datetime import datetime, timedelta, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from auth.models import (
    UserCreate, UserLogin, User, UserResponse,
    Token, UserRole, APIKeyCreate, APIKeyResponse
)
from auth.jwt import (
    verify_password, create_access_token, create_refresh_token,
    ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
)
from auth.dependencies import get_current_user, require_admin, TokenData
from auth.repository import user_repo

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_create: UserCreate,
    current_user: TokenData = Depends(require_admin)
):
    """Register a new user (admin only)."""
    # Check if user already exists
    existing_user = await user_repo.get_by_username(user_create.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    existing_email = await user_repo.get_by_email(user_create.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user = await user_repo.create(user_create)
    
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login=user.last_login
    )


@router.post("/login", response_model=Token)
async def login(user_login: UserLogin):
    """Authenticate user and return JWT tokens."""
    # Get user
    user = await user_repo.get_by_username(user_login.username)
    
    if not user or not verify_password(user_login.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    # Update last login
    await user_repo.update_last_login(user.username)
    
    # Create tokens
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.value}
    )
    refresh_token = create_refresh_token(
        data={"sub": user.username, "role": user.role.value}
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        refresh_token=refresh_token
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str):
    """Refresh access token using refresh token."""
    from auth.jwt import decode_token
    
    token_data = decode_token(refresh_token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Create new access token
    access_token = create_access_token(
        data={"sub": token_data.username, "role": token_data.role.value}
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: TokenData = Depends(get_current_user)):
    """Get current authenticated user information."""
    user = await user_repo.get_by_username(current_user.username)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login=user.last_login
    )


@router.post("/api-key", response_model=APIKeyResponse)
async def create_api_key(
    api_key_create: APIKeyCreate,
    current_user: TokenData = Depends(get_current_user)
):
    """Create a new API key for programmatic access."""
    # Generate secure API key
    api_key = f"arb_{secrets.token_urlsafe(32)}"
    
    # Store API key for user
    await user_repo.set_api_key(current_user.username, api_key)
    
    expires_at = datetime.now(timezone.utc) + timedelta(days=api_key_create.expires_in_days)
    
    return APIKeyResponse(
        api_key=api_key,
        name=api_key_create.name,
        expires_at=expires_at
    )


@router.get("/users", response_model=List[UserResponse])
async def list_users(current_user: TokenData = Depends(require_admin)):
    """List all users (admin only)."""
    users = await user_repo.list_all()
    
    return [
        UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.last_login
        )
        for user in users
    ]


@router.delete("/users/{username}")
async def delete_user(
    username: str,
    current_user: TokenData = Depends(require_admin)
):
    """Delete a user (admin only)."""
    if username == current_user.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    deleted = await user_repo.delete(username)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": f"User {username} deleted successfully"}
