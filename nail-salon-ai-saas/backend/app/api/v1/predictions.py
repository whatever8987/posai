"""
Predictions API - Phase 4: Predictive Analytics

Endpoints for revenue forecasting, churn prediction, capacity planning, and trend analysis
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import date

from app.core.database import get_db
from app.core.security import get_current_user, CurrentUser
from app.services.forecasting import ForecastingService

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.get("/dashboard")
async def get_dashboard_predictions(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive predictions for dashboard
    
    Returns:
    - Revenue forecasts (7 and 30 days)
    - Booking demand predictions
    - Churn risk analysis
    - Service trends
    - Revenue trends
    """
    try:
        tenant_schema = f"tenant_{current_user.tenant_id}"
        service = ForecastingService(tenant_schema, db, current_user.tenant_id)
        
        predictions = await service.generate_dashboard_predictions()
        
        return predictions
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating predictions: {str(e)}")


@router.post("/revenue/forecast")
async def forecast_revenue(
    days_ahead: int = Query(default=30, ge=1, le=365, description="Number of days to forecast"),
    method: str = Query(default="moving_average", description="Forecast method: moving_average or prophet"),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Forecast future revenue
    
    Methods:
    - **moving_average**: Fast, simple baseline (Week 1 Quick Win)
    - **prophet**: ML-based time series with seasonality (Week 2)
    
    Parameters:
    - **days_ahead**: Number of days to forecast (1-365)
    - **method**: Forecasting method
    
    Returns:
    - Daily revenue predictions
    - Confidence intervals
    - Summary statistics
    """
    try:
        if method not in ["moving_average", "prophet"]:
            raise HTTPException(status_code=400, detail="Method must be 'moving_average' or 'prophet'")
        
        tenant_schema = f"tenant_{current_user.tenant_id}"
        service = ForecastingService(tenant_schema, db, current_user.tenant_id)
        
        forecast = await service.forecast_revenue(days_ahead=days_ahead, method=method)
        
        if not forecast.get('success'):
            raise HTTPException(status_code=400, detail=forecast.get('error', 'Forecast failed'))
        
        return forecast
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error forecasting revenue: {str(e)}")


@router.get("/revenue/anomalies")
async def detect_revenue_anomalies(
    days_back: int = Query(default=30, ge=7, le=90, description="Days to analyze"),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Detect unusual revenue patterns (spikes or drops)
    
    Uses statistical anomaly detection to identify days with unusual revenue
    """
    try:
        tenant_schema = f"tenant_{current_user.tenant_id}"
        service = ForecastingService(tenant_schema, db, current_user.tenant_id)
        
        anomalies = await service.get_revenue_anomalies(days_back=days_back)
        
        return anomalies
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting anomalies: {str(e)}")


@router.post("/bookings/forecast")
async def forecast_booking_demand(
    days_ahead: int = Query(default=7, ge=1, le=30, description="Number of days to forecast"),
    include_hourly: bool = Query(default=False, description="Include hourly patterns"),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Predict booking demand
    
    Returns:
    - Daily booking volume predictions
    - Service type breakdown
    - Peak hours identification (if include_hourly=true)
    
    Use this to optimize staffing and capacity
    """
    try:
        tenant_schema = f"tenant_{current_user.tenant_id}"
        service = ForecastingService(tenant_schema, db, current_user.tenant_id)
        
        forecast = await service.predict_booking_demand(
            days_ahead=days_ahead,
            include_hourly=include_hourly
        )
        
        if not forecast.get('success'):
            raise HTTPException(status_code=400, detail=forecast.get('error', 'Forecast failed'))
        
        return forecast
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error forecasting bookings: {str(e)}")


@router.post("/churn/identify")
async def identify_churn_risk(
    method: str = Query(default="rule_based", description="Method: rule_based or random_forest"),
    threshold: float = Query(default=0.7, ge=0.0, le=1.0, description="Risk threshold"),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Identify customers at risk of churning
    
    Methods:
    - **rule_based**: Fast, business rule scoring (Week 1 Quick Win)
    - **random_forest**: ML classifier with feature importance (Week 2)
    
    Returns:
    - High-risk customers list
    - Churn risk scores (0-1)
    - Risk factors for each customer
    - Actionable retention recommendations
    """
    try:
        if method not in ["rule_based", "random_forest"]:
            raise HTTPException(status_code=400, detail="Method must be 'rule_based' or 'random_forest'")
        
        tenant_schema = f"tenant_{current_user.tenant_id}"
        service = ForecastingService(tenant_schema, db, current_user.tenant_id)
        
        churn_analysis = await service.identify_churn_risk(method=method, threshold=threshold)
        
        if not churn_analysis.get('success'):
            raise HTTPException(status_code=400, detail=churn_analysis.get('error', 'Analysis failed'))
        
        return churn_analysis
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error identifying churn risk: {str(e)}")


@router.get("/clv/calculate")
async def calculate_customer_lifetime_value(
    customer_id: Optional[int] = Query(default=None, description="Specific customer ID (optional)"),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate Customer Lifetime Value (CLV)
    
    CLV = Average Transaction Value × Purchase Frequency × Customer Lifespan
    
    Parameters:
    - **customer_id**: Optional - Calculate for specific customer, or get top customers if not provided
    
    Returns:
    - Historical CLV (actual value so far)
    - Predicted CLV (3-year projection)
    - Customer segments (VIP, High Value, Medium, Low)
    """
    try:
        tenant_schema = f"tenant_{current_user.tenant_id}"
        service = ForecastingService(tenant_schema, db, current_user.tenant_id)
        
        clv_data = await service.calculate_customer_lifetime_value(customer_id=customer_id)
        
        if not clv_data.get('success'):
            raise HTTPException(status_code=400, detail=clv_data.get('error', 'Calculation failed'))
        
        return clv_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating CLV: {str(e)}")


@router.post("/capacity/plan")
async def plan_capacity(
    target_date: date = Query(..., description="Date to plan for"),
    available_staff: Optional[int] = Query(default=None, description="Current staff count"),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate capacity planning recommendations
    
    Analyzes booking demand and suggests optimal staffing levels
    
    Parameters:
    - **target_date**: Date to optimize
    - **available_staff**: Optional current staff count
    
    Returns:
    - Optimal staff count
    - Predicted utilization %
    - Staffing recommendations (add/reduce/optimal)
    """
    try:
        tenant_schema = f"tenant_{current_user.tenant_id}"
        service = ForecastingService(tenant_schema, db, current_user.tenant_id)
        
        capacity_plan = await service.plan_capacity(
            target_date=target_date,
            available_staff=available_staff
        )
        
        if not capacity_plan.get('success'):
            raise HTTPException(status_code=400, detail=capacity_plan.get('error', 'Planning failed'))
        
        return capacity_plan
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error planning capacity: {str(e)}")


@router.get("/trends/analyze")
async def analyze_trends(
    trend_type: str = Query(default="service_popularity", description="Trend type: service_popularity, revenue, or seasonal"),
    period_days: int = Query(default=90, ge=30, le=365, description="Analysis period in days"),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze business trends
    
    Trend Types:
    - **service_popularity**: Identify growing, declining, and stable services
    - **revenue**: Overall revenue trend analysis
    - **seasonal**: Monthly and weekly patterns
    
    Returns:
    - Trend direction and percentage change
    - Growing/declining services
    - Peak periods
    - Actionable insights
    """
    try:
        if trend_type not in ["service_popularity", "revenue", "seasonal"]:
            raise HTTPException(
                status_code=400,
                detail="trend_type must be 'service_popularity', 'revenue', or 'seasonal'"
            )
        
        tenant_schema = f"tenant_{current_user.tenant_id}"
        service = ForecastingService(tenant_schema, db, current_user.tenant_id)
        
        trends = await service.analyze_trends(trend_type=trend_type, period_days=period_days)
        
        if not trends.get('success'):
            raise HTTPException(status_code=400, detail=trends.get('error', 'Analysis failed'))
        
        return trends
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing trends: {str(e)}")


@router.post("/models/retrain")
async def retrain_model(
    model_type: str = Query(..., description="Model type to retrain: revenue, churn, or bookings"),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger model retraining
    
    Retrains ML models with latest data to improve accuracy
    
    Note: Simple models (moving_average, rule_based) don't need retraining
    """
    try:
        if model_type not in ["revenue", "churn", "bookings"]:
            raise HTTPException(
                status_code=400,
                detail="model_type must be 'revenue', 'churn', or 'bookings'"
            )
        
        tenant_schema = f"tenant_{current_user.tenant_id}"
        service = ForecastingService(tenant_schema, db, current_user.tenant_id)
        
        # Trigger appropriate model retraining
        if model_type == "revenue":
            result = await service.forecast_revenue(days_ahead=30, method="prophet")
        elif model_type == "churn":
            result = await service.identify_churn_risk(method="random_forest")
        else:
            result = await service.predict_booking_demand(days_ahead=7)
        
        return {
            "success": True,
            "model_type": model_type,
            "message": f"{model_type} model retrained successfully",
            "trained_at": result.get('generated_at', None)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retraining model: {str(e)}")

