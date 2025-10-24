"""
User Information Endpoints
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List

from ...core.security import get_current_user, CurrentUser

router = APIRouter(prefix="/user", tags=["user"])


class UserInfo(BaseModel):
    userId: str
    username: str
    realName: str
    avatar: str
    desc: str
    homePath: str
    roles: List[str]


@router.get("/info")
async def get_user_info(current_user: CurrentUser = Depends(get_current_user)):
    """
    Get current user information from JWT token
    Returns response in Vben Admin expected format
    """
    return {
        "code": 0,
        "data": {
            "userId": current_user.get("user_id", "unknown"),
            "username": current_user.get("username", "user"),
            "realName": current_user.get("username", "User").title(),
            "avatar": f"https://api.dicebear.com/7.x/avataaars/svg?seed={current_user.get('username', 'User')}",
            "desc": f"{current_user.get('role', 'user').title()} - Nail Salon Platform",
            "homePath": "/salon/ai-query",
            "roles": [current_user.get("role", "user")],
            "tenantId": current_user.get("tenant_id")  # Include tenant ID for API calls
        }
    }

