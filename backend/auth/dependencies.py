"""FastAPI dependencies for authentication and authorization."""
from typing import Optional
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from auth.jwt import verify_token
from auth.models import UserRole, TokenData
from auth.repository import UserRepository

# Security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """Get current authenticated user from JWT token."""
    token = credentials.credentials
    
    token_data = verify_token(token)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token_data


async def get_current_user_or_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_api_key: Optional[str] = Header(None)
) -> TokenData:
    """Get current user from JWT token or API key."""
    # Try JWT token first
    if credentials:
        token = credentials.credentials
        token_data = verify_token(token)
        if token_data:
            return token_data
    
    # Try API key
    if x_api_key:
        user_repo = UserRepository()
        user = await user_repo.get_by_api_key(x_api_key)
        if user and user.is_active:
            return TokenData(
                username=user.username,
                role=user.role,
                exp=None  # API keys don't expire via token
            )
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


class RoleChecker:
    """Dependency to check if user has required role."""
    
    def __init__(self, allowed_roles: list[UserRole]):
        self.allowed_roles = allowed_roles
    
    async def __call__(self, current_user: TokenData = Depends(get_current_user)) -> TokenData:
        """Check if current user has one of the allowed roles."""
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {', '.join([r.value for r in self.allowed_roles])}"
            )
        return current_user


# Pre-configured role checkers
require_admin = RoleChecker([UserRole.ADMIN])
require_operator = RoleChecker([UserRole.ADMIN, UserRole.OPERATOR])
require_viewer = RoleChecker([UserRole.ADMIN, UserRole.OPERATOR, UserRole.VIEWER])
