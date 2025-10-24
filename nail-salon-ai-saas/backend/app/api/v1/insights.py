"""
API endpoints for automated insights
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import UUID

from ...core.database import get_db
from ...core.security import get_current_user, CurrentUser
from ...models import Insight, InsightType, InsightSeverity, InsightStatus
from ...services.insight_engine import InsightEngine


router = APIRouter(prefix="/insights", tags=["insights"])


# Request/Response Models

class InsightResponse(BaseModel):
    """Insight response model"""
    insight_id: str
    tenant_id: str
    type: str
    severity: str
    status: str
    title: str
    description: str
    recommendation: Optional[str]
    metrics: Optional[dict]
    affected_entities: Optional[dict]
    current_value: Optional[float]
    previous_value: Optional[float]
    change_percent: Optional[float]
    generated_at: str
    viewed_at: Optional[str]
    resolved_at: Optional[str]
    data_source: Optional[str]
    confidence_score: Optional[float]


class InsightStatusUpdate(BaseModel):
    """Update insight status"""
    status: InsightStatus


class InsightGenerateResponse(BaseModel):
    """Response from generate insights"""
    success: bool
    insights_generated: int
    insights: List[InsightResponse]


@router.post("/generate", response_model=InsightGenerateResponse)
async def generate_insights(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Generate new insights for the current tenant
    
    Runs all insight checks and creates new insights in the database.
    """
    try:
        # Initialize insight engine
        engine = InsightEngine(str(current_user.tenant_id))
        
        # Generate insights
        new_insights = await engine.generate_all_insights()
        
        # Save to database
        for insight in new_insights:
            db.add(insight)
        
        await db.commit()
        
        # Return results
        return InsightGenerateResponse(
            success=True,
            insights_generated=len(new_insights),
            insights=[
                InsightResponse(**insight.to_dict())
                for insight in new_insights
            ]
        )
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate insights: {str(e)}"
        )


@router.get("", response_model=List[InsightResponse])
async def list_insights(
    status_filter: Optional[InsightStatus] = Query(None, description="Filter by status"),
    type_filter: Optional[InsightType] = Query(None, description="Filter by type"),
    severity_filter: Optional[InsightSeverity] = Query(None, description="Filter by severity"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of insights to return"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    List insights for the current tenant
    
    Can filter by status, type, and severity.
    Returns most recent insights first.
    """
    # Build query with filters
    query = select(Insight).where(Insight.tenant_id == current_user.tenant_id)
    
    if status_filter:
        query = query.where(Insight.status == status_filter)
    
    if type_filter:
        query = query.where(Insight.type == type_filter)
    
    if severity_filter:
        query = query.where(Insight.severity == severity_filter)
    
    # Order by most recent first
    query = query.order_by(Insight.generated_at.desc()).limit(limit)
    
    result = await db.execute(query)
    insights = result.scalars().all()
    
    return [InsightResponse(**insight.to_dict()) for insight in insights]


@router.get("/{insight_id}", response_model=InsightResponse)
async def get_insight(
    insight_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get a specific insight by ID
    
    Automatically marks insight as viewed.
    """
    result = await db.execute(
        select(Insight).where(
            and_(
                Insight.insight_id == UUID(insight_id),
                Insight.tenant_id == current_user.tenant_id
            )
        )
    )
    insight = result.scalar_one_or_none()
    
    if not insight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insight not found"
        )
    
    # Mark as viewed if not already
    if insight.status == InsightStatus.NEW and not insight.viewed_at:
        insight.status = InsightStatus.VIEWED
        insight.viewed_at = datetime.utcnow()
        await db.commit()
    
    return InsightResponse(**insight.to_dict())


@router.patch("/{insight_id}/status", response_model=InsightResponse)
async def update_insight_status(
    insight_id: str,
    status_update: InsightStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Update the status of an insight
    
    Allows marking insights as acknowledged, resolved, or dismissed.
    """
    result = await db.execute(
        select(Insight).where(
            and_(
                Insight.insight_id == UUID(insight_id),
                Insight.tenant_id == current_user.tenant_id
            )
        )
    )
    insight = result.scalar_one_or_none()
    
    if not insight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insight not found"
        )
    
    # Update status
    insight.status = status_update.status
    
    # Set timestamps based on status
    if status_update.status == InsightStatus.RESOLVED:
        insight.resolved_at = datetime.utcnow()
    elif status_update.status == InsightStatus.VIEWED and not insight.viewed_at:
        insight.viewed_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(insight)
    
    return InsightResponse(**insight.to_dict())


@router.delete("/{insight_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_insight(
    insight_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Delete an insight
    """
    result = await db.execute(
        select(Insight).where(
            and_(
                Insight.insight_id == UUID(insight_id),
                Insight.tenant_id == current_user.tenant_id
            )
        )
    )
    insight = result.scalar_one_or_none()
    
    if not insight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insight not found"
        )
    
    await db.execute(
        delete(Insight).where(Insight.insight_id == UUID(insight_id))
    )
    await db.commit()
    
    return None


@router.get("/stats/summary")
async def get_insights_summary(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get summary statistics about insights
    
    Returns counts by status, type, and severity.
    """
    result = await db.execute(
        select(Insight).where(Insight.tenant_id == current_user.tenant_id)
    )
    all_insights = result.scalars().all()
    
    # Count by status
    by_status = {}
    for status_val in InsightStatus:
        by_status[status_val.value] = sum(1 for i in all_insights if i.status == status_val)
    
    # Count by type
    by_type = {}
    for type_val in InsightType:
        by_type[type_val.value] = sum(1 for i in all_insights if i.type == type_val)
    
    # Count by severity
    by_severity = {}
    for severity_val in InsightSeverity:
        by_severity[severity_val.value] = sum(1 for i in all_insights if i.severity == severity_val)
    
    # Count new/unresolved
    new_count = sum(1 for i in all_insights if i.status == InsightStatus.NEW)
    unresolved_count = sum(1 for i in all_insights if i.status not in [InsightStatus.RESOLVED, InsightStatus.DISMISSED])
    
    return {
        "total_insights": len(all_insights),
        "new_insights": new_count,
        "unresolved_insights": unresolved_count,
        "by_status": by_status,
        "by_type": by_type,
        "by_severity": by_severity
    }


@router.post("/batch-update")
async def batch_update_status(
    insight_ids: List[str],
    new_status: InsightStatus,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Update status for multiple insights at once
    
    Useful for marking multiple insights as acknowledged or resolved.
    """
    updated_count = 0
    
    for insight_id in insight_ids:
        result = await db.execute(
            select(Insight).where(
                and_(
                    Insight.insight_id == UUID(insight_id),
                    Insight.tenant_id == current_user.tenant_id
                )
            )
        )
        insight = result.scalar_one_or_none()
        
        if insight:
            insight.status = new_status
            if new_status == InsightStatus.RESOLVED:
                insight.resolved_at = datetime.utcnow()
            updated_count += 1
    
    await db.commit()
    
    return {
        "success": True,
        "updated_count": updated_count,
        "requested_count": len(insight_ids)
    }

