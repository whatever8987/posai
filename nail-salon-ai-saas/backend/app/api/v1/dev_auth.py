"""
Development Authentication Endpoints
Simple auth for frontend development - matches Vben Admin's expected format
NOTE: Generates REAL JWT tokens that work with API v1 endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from uuid import uuid4

from ...core.security import create_access_token
from ...core.tenancy import set_tenant_id

router = APIRouter(prefix="/auth", tags=["dev-auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    accessToken: str


# Mock users for development (with real tenant IDs)
MOCK_USERS = {
    "admin": {
        "user_id": "dev-admin-001",
        "username": "admin",
        "email": "admin@example.com",
        "tenant_id": str(uuid4()),  # Generate a real UUID tenant ID
        "role": "admin",
        "password": "123456"
    },
    "demo": {
        "user_id": "dev-demo-001",
        "username": "demo",
        "email": "demo@example.com",
        "tenant_id": str(uuid4()),  # Generate a real UUID tenant ID
        "role": "user",
        "password": "demo123"
    }
}


@router.post("/login")
async def login(request: LoginRequest):
    """
    Development login endpoint
    Accepts predefined users and generates REAL JWT tokens
    Returns response in Vben Admin expected format
    
    Users:
    - admin / 123456
    - demo / demo123
    """
    # Check if user exists and password matches
    user = MOCK_USERS.get(request.username)
    
    if not user or user["password"] != request.password:
        raise HTTPException(
            status_code=401, 
            detail="Invalid credentials. Try: admin/123456 or demo/demo123"
        )
    
    # Generate REAL JWT token that works with API v1 endpoints
    access_token = create_access_token(
        data={
            "sub": user["user_id"],
            "tenant_id": user["tenant_id"],
            "email": user["email"],
            "role": user["role"],
            "username": user["username"]
        }
    )
    
    return {
        "code": 0,
        "data": {
            "accessToken": access_token,
            "username": user["username"],
            "realName": user["username"].title(),
            "userId": user["user_id"],
            "tenantId": user["tenant_id"],  # Frontend can use this
            "roles": [user["role"]]
        }
    }
    
    raise HTTPException(status_code=401, detail="Invalid credentials")


@router.post("/refresh")
async def refresh_token():
    """Refresh token endpoint (Vben Admin format)"""
    return {
        "code": 0,
        "data": "refreshed-token"
    }


@router.post("/logout")
async def logout():
    """Logout endpoint (Vben Admin format)"""
    return {
        "code": 0,
        "message": "Logged out successfully"
    }


@router.get("/codes")
async def get_access_codes():
    """
    Get user permission codes
    Returns all permissions for development (Vben Admin format)
    """
    return {
        "code": 0,
        "data": [
            "AC_100100",  # View dashboard
            "AC_100110",  # Manage users
            "AC_100120",  # View reports
            "*"  # Wildcard - all permissions
        ]
    }

