"""
API endpoints for POS integration management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from uuid import UUID, uuid4

from ...core.database import get_db
from ...core.security import get_current_user, CurrentUser
from ...models import Integration, Tenant
from ...services.sync_service import SyncService
from ...integrations.base_adapter import SyncMode


router = APIRouter(prefix="/integrations", tags=["integrations"])


# Request/Response Models
class IntegrationTestRequest(BaseModel):
    """Request to test an integration"""
    integration_type: str = Field(..., description="Type of integration (postgres, mysql, square, csv)")
    credentials: Dict[str, Any] = Field(..., description="Connection credentials")
    config: Optional[Dict[str, Any]] = Field(default=None, description="Additional configuration")


class IntegrationTestResponse(BaseModel):
    """Response from integration test"""
    success: bool
    error: Optional[str] = None
    message: Optional[str] = None


class IntegrationCreateRequest(BaseModel):
    """Request to create a new integration"""
    name: str = Field(..., description="Integration name")
    integration_type: str = Field(..., description="Type of integration")
    credentials: Dict[str, Any] = Field(..., description="Connection credentials")
    config: Optional[Dict[str, Any]] = Field(default=None, description="Additional configuration")
    sync_frequency_minutes: Optional[int] = Field(default=60, description="Sync frequency in minutes")


class IntegrationResponse(BaseModel):
    """Integration response"""
    integration_id: str
    name: str
    integration_type: str
    status: str
    created_at: datetime
    last_sync_at: Optional[datetime]
    next_sync_at: Optional[datetime]
    last_error: Optional[str]


class SyncRequest(BaseModel):
    """Request to sync an integration"""
    mode: str = Field(default="incremental", description="Sync mode: full or incremental")


class SyncResponse(BaseModel):
    """Response from sync operation"""
    success: bool
    tables_synced: int
    total_records: int
    errors: List[str]


@router.get("/supported", response_model=List[str])
async def get_supported_integrations():
    """Get list of supported integration types"""
    return SyncService.get_supported_integrations()


@router.post("/test", response_model=IntegrationTestResponse)
async def test_integration(
    request: IntegrationTestRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Test an integration connection before creating it
    """
    sync_service = SyncService(str(current_user.tenant_id))
    
    success, error = await sync_service.test_integration(
        request.integration_type,
        request.credentials,
        request.config
    )
    
    if success:
        return IntegrationTestResponse(
            success=True,
            message="Connection successful"
        )
    else:
        return IntegrationTestResponse(
            success=False,
            error=error
        )


@router.post("", response_model=IntegrationResponse, status_code=status.HTTP_201_CREATED)
async def create_integration(
    request: IntegrationCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Create a new POS integration
    """
    # Test connection first
    sync_service = SyncService(str(current_user.tenant_id))
    success, error = await sync_service.test_integration(
        request.integration_type,
        request.credentials,
        request.config
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Integration test failed: {error}"
        )
    
    # Create integration
    integration = Integration(
        integration_id=uuid4(),
        tenant_id=current_user.tenant_id,
        name=request.name,
        integration_type=request.integration_type,
        credentials=request.credentials,
        config=request.config or {},
        status="pending",
        sync_frequency_minutes=request.sync_frequency_minutes,
        created_at=datetime.utcnow()
    )
    
    db.add(integration)
    await db.commit()
    await db.refresh(integration)
    
    return IntegrationResponse(
        integration_id=str(integration.integration_id),
        name=integration.name,
        integration_type=integration.integration_type,
        status=integration.status,
        created_at=integration.created_at,
        last_sync_at=integration.last_sync_at,
        next_sync_at=integration.next_sync_at,
        last_error=integration.last_error
    )


@router.get("", response_model=List[IntegrationResponse])
async def list_integrations(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    List all integrations for the current tenant
    """
    result = await db.execute(
        select(Integration).where(Integration.tenant_id == current_user.tenant_id)
    )
    integrations = result.scalars().all()
    
    return [
        IntegrationResponse(
            integration_id=str(integration.integration_id),
            name=integration.name,
            integration_type=integration.integration_type,
            status=integration.status,
            created_at=integration.created_at,
            last_sync_at=integration.last_sync_at,
            next_sync_at=integration.next_sync_at,
            last_error=integration.last_error
        )
        for integration in integrations
    ]


@router.get("/{integration_id}", response_model=IntegrationResponse)
async def get_integration(
    integration_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get a specific integration
    """
    result = await db.execute(
        select(Integration).where(
            Integration.integration_id == UUID(integration_id),
            Integration.tenant_id == current_user.tenant_id
        )
    )
    integration = result.scalar_one_or_none()
    
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found"
        )
    
    return IntegrationResponse(
        integration_id=str(integration.integration_id),
        name=integration.name,
        integration_type=integration.integration_type,
        status=integration.status,
        created_at=integration.created_at,
        last_sync_at=integration.last_sync_at,
        next_sync_at=integration.next_sync_at,
        last_error=integration.last_error
    )


@router.post("/{integration_id}/sync", response_model=SyncResponse)
async def sync_integration(
    integration_id: str,
    request: SyncRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Trigger a sync for an integration
    """
    # Verify integration belongs to tenant
    result = await db.execute(
        select(Integration).where(
            Integration.integration_id == UUID(integration_id),
            Integration.tenant_id == current_user.tenant_id
        )
    )
    integration = result.scalar_one_or_none()
    
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found"
        )
    
    # Determine sync mode
    mode = SyncMode.FULL if request.mode == "full" else SyncMode.INCREMENTAL
    
    # Run sync
    sync_service = SyncService(str(current_user.tenant_id))
    sync_results = await sync_service.sync_integration(
        integration_id,
        db,
        mode
    )
    
    if not sync_results.get("success"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {sync_results.get('error')}"
        )
    
    return SyncResponse(
        success=sync_results["success"],
        tables_synced=sync_results.get("tables_synced", 0),
        total_records=sync_results.get("total_records", 0),
        errors=sync_results.get("errors", [])
    )


@router.get("/{integration_id}/status")
async def get_sync_status(
    integration_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get sync status for an integration
    """
    sync_service = SyncService(str(current_user.tenant_id))
    status = await sync_service.get_sync_status(integration_id, db)
    
    if "error" in status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=status["error"]
        )
    
    return status


@router.delete("/{integration_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_integration(
    integration_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Delete an integration
    """
    # Verify integration belongs to tenant
    result = await db.execute(
        select(Integration).where(
            Integration.integration_id == UUID(integration_id),
            Integration.tenant_id == current_user.tenant_id
        )
    )
    integration = result.scalar_one_or_none()
    
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found"
        )
    
    # Delete
    await db.execute(
        delete(Integration).where(Integration.integration_id == UUID(integration_id))
    )
    await db.commit()
    
    return None

