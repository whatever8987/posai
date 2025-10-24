"""
Authentication endpoints
"""
from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr

from ...core.database import get_db, TenantDatabase
from ...core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user,
    CurrentUser,
)
from ...core.config import settings
from ...models import Tenant, User

router = APIRouter(prefix="/auth", tags=["authentication"])


class RegisterRequest(BaseModel):
    salon_name: str
    owner_email: EmailStr
    password: str
    full_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    tenant_id: str
    user_id: str


@router.post("/register", response_model=TokenResponse)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new salon (tenant) and owner account
    """
    # Check if email already exists
    result = await db.execute(
        select(Tenant).where(Tenant.owner_email == request.owner_email)
    )
    existing_tenant = result.scalar_one_or_none()
    
    if existing_tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create tenant
    tenant = Tenant(
        salon_name=request.salon_name,
        owner_email=request.owner_email,
        subscription_tier="starter",
        subscription_status="trial",
    )
    db.add(tenant)
    await db.flush()  # Get tenant_id
    
    # Create tenant schema in database
    tenant_db = TenantDatabase(str(tenant.tenant_id))
    await tenant_db.create_schema()
    
    # Create owner user
    user = User(
        tenant_id=tenant.tenant_id,
        email=request.owner_email,
        hashed_password=get_password_hash(request.password),
        full_name=request.full_name,
        role="owner",
        is_verified=True,
    )
    db.add(user)
    
    await db.commit()
    
    # Create access token
    access_token = create_access_token(
        data={
            "sub": str(user.user_id),
            "email": user.email,
            "tenant_id": str(tenant.tenant_id),
            "role": user.role,
        }
    )
    
    return TokenResponse(
        access_token=access_token,
        tenant_id=str(tenant.tenant_id),
        user_id=str(user.user_id),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Login with email and password
    """
    # Find user
    result = await db.execute(
        select(User).where(User.email == request.email)
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )
    
    # Create access token
    access_token = create_access_token(
        data={
            "sub": str(user.user_id),
            "email": user.email,
            "tenant_id": str(user.tenant_id),
            "role": user.role,
        }
    )
    
    return TokenResponse(
        access_token=access_token,
        tenant_id=str(user.tenant_id),
        user_id=str(user.user_id),
    )


@router.get("/me")
async def get_current_user_info(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get current user information
    """
    return current_user.dict()

