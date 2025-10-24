Based on your code, I'll show you how to properly separate admin and tenant roles with different permissions in FastAPI. Here's a comprehensive solution:

## 1. Enhanced Security & Permission System

```python
# security.py
from enum import Enum
from fastapi import Depends, HTTPException, status
from typing import List, Optional

class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    TENANT_OWNER = "owner"
    TENANT_MANAGER = "manager"
    TENANT_USER = "user"

class Permission(str, Enum):
    # Admin permissions
    MANAGE_ALL_TENANTS = "manage_all_tenants"
    VIEW_ALL_DATA = "view_all_data"
    MANAGE_SYSTEM_SETTINGS = "manage_system_settings"
    
    # Tenant permissions
    MANAGE_TENANT = "manage_tenant"
    MANAGE_USERS = "manage_users"
    VIEW_ANALYTICS = "view_analytics"
    MANAGE_SUBSCRIPTION = "manage_subscription"
    
    # User permissions
    USE_AI_QUERY = "use_ai_query"
    VIEW_REPORTS = "view_reports"

# Role-Permission mapping
ROLE_PERMISSIONS = {
    UserRole.SUPER_ADMIN: list(Permission),
    UserRole.ADMIN: [
        Permission.MANAGE_ALL_TENANTS,
        Permission.VIEW_ALL_DATA,
        Permission.MANAGE_SYSTEM_SETTINGS,
    ],
    UserRole.TENANT_OWNER: [
        Permission.MANAGE_TENANT,
        Permission.MANAGE_USERS,
        Permission.VIEW_ANALYTICS,
        Permission.MANAGE_SUBSCRIPTION,
        Permission.USE_AI_QUERY,
        Permission.VIEW_REPORTS,
    ],
    UserRole.TENANT_MANAGER: [
        Permission.MANAGE_USERS,
        Permission.VIEW_ANALYTICS,
        Permission.USE_AI_QUERY,
        Permission.VIEW_REPORTS,
    ],
    UserRole.TENANT_USER: [
        Permission.USE_AI_QUERY,
        Permission.VIEW_REPORTS,
    ],
}

async def get_current_user(request: Request) -> dict:
    """Enhanced current user with role and permissions"""
    # Your existing JWT logic here
    user_data = await get_current_user_from_token(request)
    
    # Add permissions to user data
    user_role = UserRole(user_data.get("role", "user"))
    user_data["permissions"] = ROLE_PERMISSIONS.get(user_role, [])
    user_data["role_enum"] = user_role
    
    return user_data

# Permission dependencies
def require_permission(permission: Permission):
    """Dependency to require specific permission"""
    async def permission_dependency(current_user: dict = Depends(get_current_user)):
        user_permissions = current_user.get("permissions", [])
        if permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return current_user
    return permission_dependency

def require_role(role: UserRole):
    """Dependency to require specific role"""
    async def role_dependency(current_user: dict = Depends(get_current_user)):
        user_role = current_user.get("role_enum")
        if user_role != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' required"
            )
        return current_user
    return role_dependency

def require_any_role(roles: List[UserRole]):
    """Dependency to require any of the specified roles"""
    async def any_role_dependency(current_user: dict = Depends(get_current_user)):
        user_role = current_user.get("role_enum")
        if user_role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of roles {[r.value for r in roles]} required"
            )
        return current_user
    return any_role_dependency
```

## 2. Admin-Specific Routes

```python
# admin.py
from fastapi import APIRouter, Depends, Query
from typing import List, Optional

from ..core.security import (
    get_current_user, 
    require_permission, 
    require_role,
    UserRole,
    Permission,
    CurrentUser
)

router = APIRouter(prefix="/admin", tags=["admin"])

class AdminUserInfo(BaseModel):
    user_id: str
    email: str
    full_name: str
    role: str
    tenant_id: str
    is_active: bool
    created_at: str

class TenantStats(BaseModel):
    tenant_id: str
    salon_name: str
    subscription_tier: str
    subscription_status: str
    user_count: int
    query_count: int
    monthly_query_limit: int
    is_active: bool

@router.get("/tenants", response_model=List[TenantStats])
async def list_all_tenants(
    current_user: CurrentUser = Depends(require_permission(Permission.MANAGE_ALL_TENANTS)),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Admin-only: List all tenants in the system
    """
    # Implementation to get all tenants with stats
    pass

@router.get("/tenants/{tenant_id}/users")
async def get_tenant_users(
    tenant_id: str,
    current_user: CurrentUser = Depends(require_permission(Permission.VIEW_ALL_DATA))
):
    """
    Admin-only: Get all users for a specific tenant
    """
    pass

@router.post("/tenants/{tenant_id}/suspend")
async def suspend_tenant(
    tenant_id: str,
    current_user: CurrentUser = Depends(require_role(UserRole.SUPER_ADMIN))
):
    """
    Super-admin only: Suspend a tenant
    """
    pass

@router.get("/system/stats")
async def get_system_stats(
    current_user: CurrentUser = Depends(require_permission(Permission.VIEW_ALL_DATA))
):
    """
    Admin: Get system-wide statistics
    """
    return {
        "total_tenants": 0,
        "active_tenants": 0,
        "total_users": 0,
        "total_queries": 0,
    }
```

## 3. Tenant Management Routes

```python
# tenant_management.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List

from ..core.security import (
    get_current_user, 
    require_permission, 
    Permission,
    UserRole,
    require_any_role,
    CurrentUser
)
from .tenancy import get_current_tenant_id

router = APIRouter(prefix="/tenant", tags=["tenant-management"])

class CreateUserRequest(BaseModel):
    email: str
    full_name: str
    role: UserRole
    send_invite: bool = True

@router.get("/users", response_model=List[AdminUserInfo])
async def get_tenant_users(
    current_user: CurrentUser = Depends(require_permission(Permission.MANAGE_USERS)),
    tenant_id: str = Depends(get_current_tenant_id)
):
    """
    Tenant owner/manager: Get all users in current tenant
    """
    # Implementation to get users for current tenant only
    pass

@router.post("/users")
async def create_tenant_user(
    user_data: CreateUserRequest,
    current_user: CurrentUser = Depends(require_permission(Permission.MANAGE_USERS)),
    tenant_id: str = Depends(get_current_tenant_id)
):
    """
    Tenant owner/manager: Create new user in current tenant
    Role restrictions apply
    """
    # Prevent users from creating higher-privilege accounts
    current_user_role = current_user.get("role_enum")
    requested_role = user_data.role
    
    role_hierarchy = {
        UserRole.TENANT_OWNER: [UserRole.TENANT_OWNER, UserRole.TENANT_MANAGER, UserRole.TENANT_USER],
        UserRole.TENANT_MANAGER: [UserRole.TENANT_MANAGER, UserRole.TENANT_USER],
        UserRole.TENANT_USER: [UserRole.TENANT_USER]
    }
    
    if requested_role not in role_hierarchy.get(current_user_role, []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create user with higher role than your own"
        )
    
    # Create user implementation
    pass

@router.get("/analytics")
async def get_tenant_analytics(
    current_user: CurrentUser = Depends(require_permission(Permission.VIEW_ANALYTICS)),
    tenant_id: str = Depends(get_current_tenant_id)
):
    """
    Tenant analytics - accessible to managers and owners
    """
    pass
```

## 4. Enhanced User Routes with Role-Based Responses

```python
# user.py - Enhanced version
@router.get("/info")
async def get_user_info(current_user: CurrentUser = Depends(get_current_user)):
    """
    Get current user information with role-based data
    """
    base_info = {
        "userId": current_user.get("user_id", "unknown"),
        "username": current_user.get("username", "user"),
        "realName": current_user.get("username", "User").title(),
        "avatar": f"https://api.dicebear.com/7.x/avataaars/svg?seed={current_user.get('username', 'User')}",
        "desc": f"{current_user.get('role', 'user').title()} - Nail Salon Platform",
        "homePath": "/salon/ai-query",
        "roles": [current_user.get("role", "user")],
        "tenantId": current_user.get("tenant_id"),
        "permissions": current_user.get("permissions", [])  # Include permissions for frontend
    }
    
    # Role-specific home paths
    user_role = current_user.get("role", "user")
    if user_role in ["super_admin", "admin"]:
        base_info["homePath"] = "/admin/dashboard"
    elif user_role == "owner":
        base_info["homePath"] = "/salon/management"
    elif user_role == "manager":
        base_info["homePath"] = "/salon/analytics"
    
    return {
        "code": 0,
        "data": base_info
    }

@router.get("/permissions")
async def get_user_permissions(current_user: CurrentUser = Depends(get_current_user)):
    """
    Get current user's permissions
    """
    return {
        "code": 0,
        "data": {
            "permissions": current_user.get("permissions", []),
            "role": current_user.get("role")
        }
    }
```

## 5. User-Specific Routes

```python
# user_actions.py
from fastapi import APIRouter, Depends

from ..core.security import (
    get_current_user, 
    require_permission, 
    Permission,
    CurrentUser
)

router = APIRouter(prefix="/user", tags=["user-actions"])

@router.post("/ai-query")
async def submit_ai_query(
    query_data: dict,
    current_user: CurrentUser = Depends(require_permission(Permission.USE_AI_QUERY)),
    tenant_id: str = Depends(get_current_tenant_id)
):
    """
    Regular user: Submit AI query (available to all authenticated users)
    """
    # Check tenant query limits
    # Increment query count
    # Process AI query
    pass

@router.get("/reports")
async def get_user_reports(
    current_user: CurrentUser = Depends(require_permission(Permission.VIEW_REPORTS)),
    tenant_id: str = Depends(get_current_tenant_id)
):
    """
    Get reports accessible to the current user
    """
    pass
```

## 6. Main Router Organization

```python
# api.py - Main router
from fastapi import APIRouter
from .auth import router as auth_router
from .admin import router as admin_router
from .tenant_management import router as tenant_management_router
from .user import router as user_router
from .user_actions import router as user_actions_router

api_router = APIRouter()

# Public routes
api_router.include_router(auth_router)

# User routes (require authentication)
api_router.include_router(user_router)
api_router.include_router(user_actions_router)

# Tenant management routes (require tenant context + permissions)
api_router.include_router(tenant_management_router)

# Admin routes (require admin permissions)
api_router.include_router(admin_router)
```

## 7. Enhanced Tenant Middleware

```python
# tenancy.py - Enhanced version
# Add this to your existing TenantMiddleware

class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # ... existing tenant resolution logic ...
        
        # After setting tenant_id, verify user has access to this tenant
        if tenant_id and request.headers.get("Authorization"):
            try:
                current_user = await get_current_user(request)
                user_tenant_id = current_user.get("tenant_id")
                user_role = current_user.get("role_enum")
                
                # Admin users can access any tenant
                if user_role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
                    if user_tenant_id != tenant_id:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="Access to this tenant not permitted"
                        )
            except HTTPException:
                # Let auth dependencies handle authentication errors
                pass
        
        # Continue with existing logic...
```

This structure provides:

1. **Clear separation** between admin, tenant management, and user routes
2. **Role-based permissions** with hierarchical access control
3. **Tenant isolation** ensuring users can only access their own tenant data
4. **Flexible permission system** that can be extended
5. **Frontend-friendly** permission data in user info

Admins get system-wide access, tenant owners/managers get tenant-level administrative access, and regular users get basic application functionality.