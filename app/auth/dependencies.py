"""
FastAPI dependencies for authentication.

Provides reusable dependencies for protecting endpoints.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import AuthService
from app.auth.schemas import TokenData
from app.database.database import get_db
from app.database.models import User
from app.utils.logger import logger


# HTTP Bearer token security scheme
# This adds the "Authorize" button in Swagger UI
security = HTTPBearer(
    scheme_name="JWT",
    description="Enter your JWT token obtained from /auth/login"
)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user.
    
    Validates the JWT token and returns the user from database.
    
    Args:
        credentials: Bearer token from Authorization header
        db: Database session
        
    Returns:
        User object for the authenticated user
        
    Raises:
        HTTPException 401: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    
    # Decode and validate token
    payload = AuthService.decode_token(token)
    if payload is None:
        logger.warning("Invalid or expired JWT token")
        raise credentials_exception
    
    # Extract user email from token
    email: str = payload.get("sub")
    if email is None:
        logger.warning("JWT token missing 'sub' claim")
        raise credentials_exception
    
    # Get user from database
    user = await AuthService.get_user_by_email(db, email)
    if user is None:
        logger.warning(f"User not found for token: {email}")
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get the current ACTIVE authenticated user.
    
    Extends get_current_user to also check if user is active.
    
    Args:
        current_user: User from get_current_user dependency
        
    Returns:
        User object if active
        
    Raises:
        HTTPException 403: If user account is disabled
    """
    if not current_user.is_active:
        logger.warning(f"Disabled user attempted access: {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    return current_user


def require_role(required_role: str):
    """
    Dependency factory to require a specific role.
    
    Usage:
        @app.get("/admin-only")
        async def admin_endpoint(user: User = Depends(require_role("admin"))):
            ...
    
    Args:
        required_role: Role required to access the endpoint
        
    Returns:
        Dependency function that checks user role
    """
    async def role_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if current_user.role != required_role:
            logger.warning(
                f"User {current_user.email} with role '{current_user.role}' "
                f"attempted to access endpoint requiring '{required_role}'"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This endpoint requires '{required_role}' role"
            )
        return current_user
    
    return role_checker
