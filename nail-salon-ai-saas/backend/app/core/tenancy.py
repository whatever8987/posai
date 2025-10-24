"""
Tenant context management and middleware
"""
from contextvars import ContextVar
from typing import Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from jose import jwt, JWTError

from .config import settings

# Context variable to store current tenant ID
_tenant_id: ContextVar[Optional[str]] = ContextVar("tenant_id", default=None)


def get_current_tenant_id() -> Optional[str]:
    """Get the current tenant ID from context"""
    return _tenant_id.get()


def set_tenant_id(tenant_id: str):
    """Set the tenant ID in context"""
    _tenant_id.set(tenant_id)


def clear_tenant_id():
    """Clear the tenant ID from context"""
    _tenant_id.set(None)


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract and set tenant context from requests
    Tenant ID can come from:
    1. X-Tenant-ID header
    2. JWT token claims
    3. API key
    """
    
    async def dispatch(self, request: Request, call_next):
        # Skip tenant resolution for public endpoints
        public_paths = [
            "/",
            "/health",
            "/docs",
            "/openapi.json",
            "/api/v1/openapi.json",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/auth/login",      # Dev auth endpoint
            "/api/auth/refresh",    # Dev auth endpoint
            "/api/auth/logout",     # Dev auth endpoint
            "/api/auth/codes",      # Dev auth endpoint
        ]
        
        # Skip browser icon requests and static files
        skip_paths = [
            "/favicon.ico",
            "/apple-touch-icon.png",
            "/apple-touch-icon-precomposed.png",
        ]
        
        # Check if path should be skipped
        current_path = request.url.path
        
        if (current_path in public_paths or 
            current_path in skip_paths or
            any(current_path.startswith(path) for path in public_paths) or
            any(current_path.endswith(ext) for ext in ['.ico', '.png', '.jpg', '.css', '.js'])):
            response = await call_next(request)
            return response
        
        # Try to get tenant ID from header
        tenant_id = request.headers.get("X-Tenant-ID")
        
        # If not in header, try to extract from JWT token in Authorization header
        if not tenant_id:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                try:
                    # Decode JWT token to get tenant_id
                    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
                    tenant_id = payload.get("tenant_id")
                except JWTError:
                    # Token is invalid, but let the auth dependency handle it
                    pass
        
        # If still no tenant ID, try from request state (set by previous middleware)
        if not tenant_id:
            tenant_id = getattr(request.state, "tenant_id", None)
        
        # For authenticated endpoints, allow request to proceed without tenant_id
        # The auth dependency will validate the token and raise 401 if invalid
        # This allows JWT-based authentication to work properly
        if not tenant_id:
            # Check if this is an authenticated endpoint (has Authorization header)
            if request.headers.get("Authorization"):
                # Let it through - the endpoint's auth dependency will handle validation
                response = await call_next(request)
                return response
            
            # No tenant ID and no auth header - reject
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant ID not provided. Include X-Tenant-ID header or valid JWT token."
            )
        
        # Set tenant context
        set_tenant_id(tenant_id)
        
        try:
            response = await call_next(request)
            return response
        finally:
            # Clear tenant context after request
            clear_tenant_id()


class TenantContext:
    """
    Context manager for tenant operations
    Usage:
        async with TenantContext(tenant_id) as ctx:
            # All database operations here will use tenant schema
            session = await ctx.get_session()
    """
    
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.previous_tenant_id = None
    
    async def __aenter__(self):
        self.previous_tenant_id = get_current_tenant_id()
        set_tenant_id(self.tenant_id)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.previous_tenant_id:
            set_tenant_id(self.previous_tenant_id)
        else:
            clear_tenant_id()
    
    def get_tenant_id(self) -> str:
        return self.tenant_id