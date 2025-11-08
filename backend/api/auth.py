"""
Authentication and Security Module

Handles JWT authentication, password hashing, and user management.
Includes rate limiting and security middleware.

Created by: Anton Alexander
Date: November 8, 2025
"""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import bcrypt
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Dict
from pydantic import BaseModel, EmailStr
import secrets

# Security configuration
SECRET_KEY = secrets.token_urlsafe(32)  # In production, use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# HTTP Bearer token scheme
security = HTTPBearer()


# Pydantic models
class User(BaseModel):
    """User model"""
    username: str
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    disabled: bool = False
    is_admin: bool = False


class UserInDB(User):
    """User model with hashed password"""
    hashed_password: str


class Token(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str
    expires_in: int
    user: User


class TokenData(BaseModel):
    """Token data extracted from JWT"""
    username: Optional[str] = None


class LoginRequest(BaseModel):
    """Login request model"""
    username: str
    password: str


class RegisterRequest(BaseModel):
    """Registration request model"""
    username: str
    password: str
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None


# Demo users database (in production, use real database)
demo_users_db: Dict[str, UserInDB] = {
    "admin": UserInDB(
        username="admin",
        email="admin@example.com",
        full_name="Admin User",
        disabled=False,
        is_admin=True,
        hashed_password="$2b$12$8z8QqI60gVvA5ipXG2wRSOv7SeAmd3fUz7TsTui/qNwiXhG5ILIcK"  # "admin"
    ),
    "demo": UserInDB(
        username="demo",
        email="demo@example.com",
        full_name="Demo User",
        disabled=False,
        is_admin=False,
        hashed_password="$2b$12$Y1QHRfN4k4sGesvLJgUEjeadg810pR6ofIu7.MISrUjrsS4b39H8G"  # "demo123"
    ),
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash using bcrypt"""
    # Convert to bytes
    password_bytes = plain_password.encode('utf-8')
    hash_bytes = hashed_password.encode('utf-8')

    # Bcrypt has a 72-byte limit
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]

    return bcrypt.checkpw(password_bytes, hash_bytes)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt"""
    password_bytes = password.encode('utf-8')

    # Bcrypt has a 72-byte limit
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]

    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def get_user(username: str) -> Optional[UserInDB]:
    """Get user from database"""
    return demo_users_db.get(username)


def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """Authenticate a user"""
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception

    # Convert UserInDB to User (exclude hashed_password)
    return User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        disabled=user.disabled,
        is_admin=user.is_admin
    )


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user"""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current admin user"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


def register_user(username: str, password: str, email: Optional[str] = None, full_name: Optional[str] = None) -> User:
    """Register a new user"""
    if username in demo_users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    hashed_password = get_password_hash(password)
    new_user = UserInDB(
        username=username,
        email=email,
        full_name=full_name,
        disabled=False,
        is_admin=False,
        hashed_password=hashed_password
    )

    demo_users_db[username] = new_user

    return User(
        username=new_user.username,
        email=new_user.email,
        full_name=new_user.full_name,
        disabled=new_user.disabled,
        is_admin=new_user.is_admin
    )


# Rate limiting (simple in-memory implementation)
class RateLimiter:
    """Simple rate limiter"""
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, list] = {}

    async def check_rate_limit(self, request: Request):
        """Check if request exceeds rate limit"""
        client_ip = request.client.host
        now = datetime.utcnow()

        if client_ip not in self.requests:
            self.requests[client_ip] = []

        # Remove old requests (older than 1 minute)
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if (now - req_time).total_seconds() < 60
        ]

        if len(self.requests[client_ip]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later."
            )

        self.requests[client_ip].append(now)


# Create global rate limiter
rate_limiter = RateLimiter(requests_per_minute=60)
