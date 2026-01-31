"""
Authentication router with login and user info endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import LoginRequest, TokenResponse, UserResponse
from app.auth.service import AuthService
from app.auth.dependencies import get_current_active_user
from app.database.database import get_db
from app.database.models import User
from app.config import settings
from app.utils.logger import logger
from app.auth.dependencies import get_current_user


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login with email and password",
    description="Authenticate with admin credentials and receive a JWT token."
)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and return JWT token.
    
    The token should be included in subsequent requests as:
    `Authorization: Bearer <token>`
    
    Token is valid for 24 hours by default.
    """
    logger.info(f"Login attempt for: {request.email}")
    
    # Authenticate against database
    user = await AuthService.authenticate_user(
        db=db,
        email=request.email,
        password=request.password
    )
    
    if not user:
        logger.warning(f"Failed login attempt for: {request.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create JWT token with user info
    access_token = AuthService.create_access_token(
        data={
            "sub": user.email,
            "user_id": user.id,
            "role": user.role
        }
    )
    
    logger.info(f"Login successful for: {user.email}")
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.jwt_expiration_hours * 3600  # Convert hours to seconds
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user info",
    description="Returns information about the currently authenticated user."
)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get information about the currently authenticated user.
    
    Requires valid JWT token in Authorization header.
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role,
        is_active=bool(current_user.is_active),
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )


@router.get(
    "/seed-admin",
    summary="Create initial admin user",
    description="Creates the admin user from environment variables. Can only be called once.",
    include_in_schema=True  # Visible in docs for initial setup
)
async def seed_admin_user(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)  # 🔐 Protected Endpoint
):
    """
    Seed the database with the initial admin user.
    
    Uses ADMIN_EMAIL and ADMIN_PASSWORD from environment variables.
    Returns error if admin already exists.
    """
    logger.info("Attempting to seed admin user...")
    
    try:
        admin = await AuthService.create_admin_user(db)
        
        if admin is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Admin user already exists: {settings.admin_email}"
            )
        
        return {
            "message": "Admin user created successfully",
            "email": admin.email,
            "role": admin.role
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Seed error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Seed failed: {str(e)}"
        )
