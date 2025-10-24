"""
Security utilities for authentication and authorization
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .config import settings

# Password hashing - Use django_pbkdf2_sha256 as reliable fallback
pwd_context = CryptContext(schemes=["django_pbkdf2_sha256", "bcrypt"], deprecated="auto")

# Bearer token scheme
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decode and verify JWT token
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


class CurrentUser:
    """
    User object returned by authentication
    Provides both dict-like and attribute access for compatibility
    """
    def __init__(self, user_data: Dict[str, Any]):
        self._data = user_data
        # Set attributes for object-style access
        self.user_id = user_data.get("user_id") or user_data.get("sub")
        self.tenant_id = user_data.get("tenant_id")
        self.email = user_data.get("email")
        self.role = user_data.get("role", "user")
        self.username = user_data.get("username")
    
    def get(self, key: str, default=None):
        """Dict-style access"""
        return self._data.get(key, default)
    
    def __getitem__(self, key: str):
        """Dict-style access with []"""
        return self._data[key]
    
    def dict(self):
        """Return as dictionary"""
        return self._data.copy()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> CurrentUser:
    """
    Dependency to get current authenticated user from JWT token
    Returns a CurrentUser object that supports both attribute and dict access
    """
    token = credentials.credentials
    payload = decode_access_token(token)
    
    user_id: str = payload.get("sub")
    tenant_id: str = payload.get("tenant_id")
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    
    user_data = {
        "user_id": user_id,
        "sub": user_id,
        "tenant_id": tenant_id,
        "email": payload.get("email"),
        "role": payload.get("role", "user"),
        "username": payload.get("username", user_id),
    }
    
    return CurrentUser(user_data)


def check_permissions(required_role: str):
    """
    Dependency factory for role-based access control
    
    Usage:
        @app.get("/admin")
        async def admin_route(user = Depends(check_permissions("admin"))):
            ...
    """
    async def permission_checker(
        user: CurrentUser = Depends(get_current_user)
    ) -> CurrentUser:
        role_hierarchy = {
            "user": 1,
            "manager": 2,
            "admin": 3,
            "owner": 4,
        }
        
        user_role_level = role_hierarchy.get(user.role or "user", 0)
        required_level = role_hierarchy.get(required_role, 999)
        
        if user_role_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        return user
    
    return permission_checker


def generate_api_key() -> str:
    """Generate a random API key for integrations"""
    import secrets
    return f"nsa_{secrets.token_urlsafe(32)}"


def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage"""
    return get_password_hash(api_key)


def verify_api_key(api_key: str, hashed_key: str) -> bool:
    """Verify an API key against its hash"""
    return verify_password(api_key, hashed_key)