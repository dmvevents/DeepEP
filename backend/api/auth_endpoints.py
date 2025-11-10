"""
Authentication API Endpoints

FastAPI endpoints for user authentication, registration, and profile management.

Created by: Anton Alexander
Date: November 8, 2025
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from datetime import timedelta
from auth import (
    User,
    Token,
    LoginRequest,
    RegisterRequest,
    authenticate_user,
    create_access_token,
    register_user,
    get_current_active_user,
    get_current_admin_user,
    rate_limiter,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

# Create router
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token, summary="Login to get access token")
async def login(
    login_data: LoginRequest,
    request: Request
):
    """
    Login with username and password to get JWT access token.

    **Demo Accounts:**
    - Username: `admin`, Password: `admin` (Admin user)
    - Username: `demo`, Password: `demo123` (Regular user)
    """
    # Check rate limit
    await rate_limiter.check_rate_limit(request)

    # Authenticate user
    user = authenticate_user(login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # in seconds
        user=User(
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            disabled=user.disabled,
            is_admin=user.is_admin
        )
    )


@router.post("/register", response_model=User, summary="Register new user")
async def register(
    register_data: RegisterRequest,
    request: Request
):
    """
    Register a new user account.

    **Requirements:**
    - Username: 3-20 characters
    - Password: Minimum 6 characters
    - Email: Valid email format (optional)
    """
    # Check rate limit
    await rate_limiter.check_rate_limit(request)

    # Validate input
    if len(register_data.username) < 3 or len(register_data.username) > 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must be between 3 and 20 characters"
        )

    if len(register_data.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters"
        )

    # Register user
    try:
        new_user = register_user(
            username=register_data.username,
            password=register_data.password,
            email=register_data.email,
            full_name=register_data.full_name
        )
        return new_user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.get("/me", response_model=User, summary="Get current user profile")
async def read_users_me(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get the current authenticated user's profile.

    **Requires:** Valid JWT token in Authorization header
    """
    return current_user


@router.get("/verify", summary="Verify token validity")
async def verify_token(
    current_user: User = Depends(get_current_active_user)
):
    """
    Verify that the provided token is valid.

    **Returns:** User information if token is valid
    """
    return {
        "valid": True,
        "user": current_user
    }


@router.get("/admin/users", summary="Get all users (Admin only)")
async def get_all_users(
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get list of all users.

    **Requires:** Admin privileges
    """
    from auth import demo_users_db

    users = [
        User(
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            disabled=user.disabled,
            is_admin=user.is_admin
        )
        for user in demo_users_db.values()
    ]

    return {
        "total": len(users),
        "users": users
    }


@router.post("/logout", summary="Logout (client-side token invalidation)")
async def logout():
    """
    Logout endpoint.

    Since we're using JWT tokens, logout is handled client-side by:
    1. Removing the token from localStorage/sessionStorage
    2. Clearing any cached user data

    **Note:** Server-side token blacklisting can be implemented with Redis for production.
    """
    return {
        "message": "Logged out successfully",
        "action": "Remove token from client storage"
    }
