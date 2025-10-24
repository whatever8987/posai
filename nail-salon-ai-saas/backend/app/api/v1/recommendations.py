"""
Recommendations API - Phase 5: AI-Powered Business Recommendations

Endpoints for generating and managing business recommendations
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from ...core.security import CurrentUser
from app.models.recommendation import (
    Recommendation,
    RecommendationType,
    RecommendationPriority,
    RecommendationStatus
)
from app.services.recommendation_engine import RecommendationEngine

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/generate")
async def generate_all_recommendations(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate all types of AI-powered recommendations
    
    Returns comprehensive recommendations across all categories:
    - Promotions (based on trends + capacity)
    - Scheduling (based on demand forecasts)
    - Retention (based on churn predictions)
    - Inventory (based on usage rates)
    - Pricing (based on demand elasticity)
    
    Each recommendation includes:
    - Title and description
    - Priority level (critical/high/medium/low)
    - Specific action items
    - Expected business impact
    - Confidence score
    """
    try:
        tenant_schema = f"tenant_{current_user.tenant_id}"
        engine = RecommendationEngine(tenant_schema, db, current_user.tenant_id)
        
        recommendations = await engine.generate_all_recommendations()
        
        if not recommendations.get('success'):
            raise HTTPException(
                status_code=500,
                detail=recommendations.get('error', 'Failed to generate recommendations')
            )
        
        return recommendations
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating recommendations: {str(e)}"
        )


@router.get("/promotions")
async def get_promotion_recommendations(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get promotion recommendations
    
    Suggests promotional campaigns based on:
    - Service trends (promote growing services)
    - Capacity gaps (fill slow periods)
    - Seasonal patterns
    
    Example recommendations:
    - "Capitalize on Gel Manicure trend (up 23%)"
    - "Fill slow time slots with targeted promotions"
    - "Prepare seasonal promotion campaign"
    """
    try:
        tenant_schema = f"tenant_{current_user.tenant_id}"
        engine = RecommendationEngine(tenant_schema, db, current_user.tenant_id)
        
        recommendations = await engine.generate_promotion_recommendations()
        
        return {
            "success": True,
            "type": "promotion",
            "count": len(recommendations),
            "recommendations": recommendations
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating promotion recommendations: {str(e)}"
        )


@router.get("/scheduling")
async def get_scheduling_recommendations(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get staff scheduling recommendations
    
    Optimizes staffing based on:
    - Booking demand forecasts
    - Staff capacity planning
    - Peak hour identification
    
    Example recommendations:
    - "Add staff for high-demand Saturday"
    - "Reduce staffing on slow Tuesday"
    - "Optimize staff schedules for peak hours"
    """
    try:
        tenant_schema = f"tenant_{current_user.tenant_id}"
        engine = RecommendationEngine(tenant_schema, db, current_user.tenant_id)
        
        recommendations = await engine.generate_scheduling_recommendations()
        
        return {
            "success": True,
            "type": "scheduling",
            "count": len(recommendations),
            "recommendations": recommendations
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating scheduling recommendations: {str(e)}"
        )


@router.get("/retention")
async def get_retention_recommendations(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get customer retention recommendations
    
    Identifies retention opportunities based on:
    - Churn predictions
    - Customer lifetime value
    - Visit patterns
    
    Example recommendations:
    - "Launch win-back campaign for 12 at-risk customers"
    - "Launch VIP loyalty program for top customers"
    - "Re-engage dormant customers"
    """
    try:
        tenant_schema = f"tenant_{current_user.tenant_id}"
        engine = RecommendationEngine(tenant_schema, db, current_user.tenant_id)
        
        recommendations = await engine.generate_retention_recommendations()
        
        return {
            "success": True,
            "type": "retention",
            "count": len(recommendations),
            "recommendations": recommendations
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating retention recommendations: {str(e)}"
        )


@router.get("/inventory")
async def get_inventory_recommendations(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get inventory management recommendations
    
    Optimizes inventory based on:
    - Usage rates
    - Stock levels
    - Revenue forecasts
    
    Example recommendations:
    - "URGENT: Reorder 5 products running out"
    - "Schedule reorder for low stock items"
    - "Increase min stock levels for popular products"
    """
    try:
        tenant_schema = f"tenant_{current_user.tenant_id}"
        engine = RecommendationEngine(tenant_schema, db, current_user.tenant_id)
        
        recommendations = await engine.generate_inventory_recommendations()
        
        return {
            "success": True,
            "type": "inventory",
            "count": len(recommendations),
            "recommendations": recommendations
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating inventory recommendations: {str(e)}"
        )


@router.get("/pricing")
async def get_pricing_recommendations(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get pricing optimization recommendations
    
    Suggests pricing strategies based on:
    - Demand elasticity
    - Service popularity
    - Competitive analysis
    
    Example recommendations:
    - "Consider pricing increase for high-demand service"
    - "Create service bundle for popular combinations"
    - "Implement dynamic pricing for off-peak times"
    """
    try:
        tenant_schema = f"tenant_{current_user.tenant_id}"
        engine = RecommendationEngine(tenant_schema, db, current_user.tenant_id)
        
        recommendations = await engine.generate_pricing_recommendations()
        
        return {
            "success": True,
            "type": "pricing",
            "count": len(recommendations),
            "recommendations": recommendations
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating pricing recommendations: {str(e)}"
        )


@router.post("/save")
async def save_recommendations(
    recommendation_type: Optional[RecommendationType] = Query(None, description="Filter by type"),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate and save recommendations to database
    
    Persists recommendations for tracking and follow-up
    """
    try:
        tenant_schema = f"tenant_{current_user.tenant_id}"
        engine = RecommendationEngine(tenant_schema, db, current_user.tenant_id)
        
        # Generate all recommendations
        all_recs = await engine.generate_all_recommendations()
        
        if not all_recs.get('success'):
            raise HTTPException(status_code=500, detail="Failed to generate recommendations")
        
        # Save to database
        saved_count = 0
        for rec_type, recs in all_recs['recommendations'].items():
            if recommendation_type and rec_type != recommendation_type.value:
                continue
                
            for rec_data in recs:
                await engine.save_recommendation(rec_data)
                saved_count += 1
        
        return {
            "success": True,
            "saved_count": saved_count,
            "message": f"Saved {saved_count} recommendations"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error saving recommendations: {str(e)}"
        )


@router.get("/history")
async def get_recommendation_history(
    status: Optional[RecommendationStatus] = Query(None, description="Filter by status"),
    limit: int = Query(default=50, ge=1, le=200, description="Number of recommendations to return"),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get historical recommendations
    
    Retrieve past recommendations with optional filtering
    """
    try:
        from sqlalchemy import select, desc
        
        query = select(Recommendation).where(
            Recommendation.tenant_id == current_user.tenant_id
        )
        
        if status:
            query = query.where(Recommendation.status == status)
        
        query = query.order_by(desc(Recommendation.created_at)).limit(limit)
        
        result = await db.execute(query)
        recommendations = result.scalars().all()
        
        return {
            "success": True,
            "count": len(recommendations),
            "recommendations": [
                {
                    "id": rec.id,
                    "type": rec.type.value,
                    "priority": rec.priority.value,
                    "status": rec.status.value,
                    "title": rec.title,
                    "description": rec.description,
                    "action_items": rec.action_items,
                    "expected_impact": rec.expected_impact,
                    "confidence_score": rec.confidence_score,
                    "created_at": rec.created_at.isoformat(),
                    "expires_at": rec.expires_at.isoformat() if rec.expires_at else None
                }
                for rec in recommendations
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving recommendation history: {str(e)}"
        )


@router.patch("/{recommendation_id}/status")
async def update_recommendation_status(
    recommendation_id: int,
    new_status: RecommendationStatus,
    feedback: Optional[dict] = None,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update recommendation status
    
    Mark recommendations as accepted, rejected, completed, or expired
    Optionally provide feedback
    """
    try:
        from sqlalchemy import select, update
        
        # Get recommendation
        query = select(Recommendation).where(
            Recommendation.id == recommendation_id,
            Recommendation.tenant_id == current_user.tenant_id
        )
        result = await db.execute(query)
        recommendation = result.scalar_one_or_none()
        
        if not recommendation:
            raise HTTPException(status_code=404, detail="Recommendation not found")
        
        # Update status
        update_data = {
            "status": new_status
        }
        
        if new_status in [RecommendationStatus.ACCEPTED, RecommendationStatus.COMPLETED]:
            update_data["acted_on_at"] = datetime.utcnow()
        
        if feedback:
            update_data["user_feedback"] = feedback
        
        query = update(Recommendation).where(
            Recommendation.id == recommendation_id
        ).values(**update_data)
        
        await db.execute(query)
        await db.commit()
        
        return {
            "success": True,
            "recommendation_id": recommendation_id,
            "new_status": new_status.value,
            "message": "Status updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating recommendation status: {str(e)}"
        )


@router.get("/dashboard")
async def get_recommendations_dashboard(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get recommendations summary for dashboard
    
    Returns:
    - Critical recommendations requiring immediate action
    - High priority recommendations
    - Summary by type
    - Recent activity
    """
    try:
        from sqlalchemy import select, func
        
        # Get active recommendations
        query = select(Recommendation).where(
            Recommendation.tenant_id == current_user.tenant_id,
            Recommendation.status == RecommendationStatus.ACTIVE
        ).order_by(
            Recommendation.priority.desc(),
            Recommendation.created_at.desc()
        )
        
        result = await db.execute(query)
        active_recommendations = result.scalars().all()
        
        # Group by priority
        critical = [r for r in active_recommendations if r.priority == RecommendationPriority.CRITICAL]
        high = [r for r in active_recommendations if r.priority == RecommendationPriority.HIGH]
        medium = [r for r in active_recommendations if r.priority == RecommendationPriority.MEDIUM]
        
        # Group by type
        by_type = {}
        for rec in active_recommendations:
            if rec.type.value not in by_type:
                by_type[rec.type.value] = []
            by_type[rec.type.value].append({
                "id": rec.id,
                "title": rec.title,
                "priority": rec.priority.value,
                "confidence_score": rec.confidence_score
            })
        
        return {
            "success": True,
            "summary": {
                "total_active": len(active_recommendations),
                "critical_count": len(critical),
                "high_count": len(high),
                "medium_count": len(medium)
            },
            "critical_recommendations": [
                {
                    "id": r.id,
                    "type": r.type.value,
                    "title": r.title,
                    "description": r.description,
                    "action_items": r.action_items,
                    "expected_impact": r.expected_impact
                }
                for r in critical[:5]  # Top 5 critical
            ],
            "high_priority_recommendations": [
                {
                    "id": r.id,
                    "type": r.type.value,
                    "title": r.title,
                    "expected_impact": r.expected_impact
                }
                for r in high[:5]  # Top 5 high
            ],
            "by_type": by_type
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving recommendations dashboard: {str(e)}"
        )

