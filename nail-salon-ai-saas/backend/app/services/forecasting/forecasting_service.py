"""
Forecasting Service - Main orchestrator for all predictive analytics

Coordinates all prediction models and provides unified interface
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, date
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from .revenue_forecaster import RevenueForecaster
from .booking_predictor import BookingPredictor
from .churn_predictor import ChurnPredictor
from .capacity_planner import CapacityPlanner
from .trend_analyzer import TrendAnalyzer

logger = logging.getLogger(__name__)


class ForecastingService:
    """
    Main service for all predictive analytics
    Provides unified interface for forecasting, predictions, and analysis
    """
    
    def __init__(self, tenant_schema: str, db: AsyncSession, tenant_id: int):
        self.tenant_schema = tenant_schema
        self.db = db
        self.tenant_id = tenant_id
        
        # Initialize all predictors
        self.revenue_forecaster = RevenueForecaster(tenant_schema, db)
        self.booking_predictor = BookingPredictor(tenant_schema, db)
        self.churn_predictor = ChurnPredictor(tenant_schema, db)
        self.capacity_planner = CapacityPlanner(tenant_schema, db)
        self.trend_analyzer = TrendAnalyzer(tenant_schema, db)
        
        self.logger = logging.getLogger(__name__)
    
    async def generate_dashboard_predictions(self) -> Dict[str, Any]:
        """
        Generate all predictions for dashboard display
        Returns comprehensive prediction data
        """
        try:
            self.logger.info(f"Generating dashboard predictions for tenant {self.tenant_id}")
            
            # Run all predictions in parallel (conceptually - for simplicity, sequential here)
            
            # 1. Revenue forecast (7 and 30 days)
            revenue_7day = await self.revenue_forecaster.predict(
                days_ahead=7,
                method="moving_average",
                tenant_id=self.tenant_id
            )
            
            revenue_30day = await self.revenue_forecaster.predict(
                days_ahead=30,
                method="moving_average",
                tenant_id=self.tenant_id
            )
            
            # 2. Booking demand forecast
            booking_forecast = await self.booking_predictor.predict(
                days_ahead=7,
                tenant_id=self.tenant_id,
                include_hourly=True
            )
            
            # 3. Churn risk analysis
            churn_analysis = await self.churn_predictor.predict(
                method="rule_based",
                threshold=0.7,
                tenant_id=self.tenant_id
            )
            
            # 4. Service trends
            service_trends = await self.trend_analyzer.predict(
                trend_type="service_popularity",
                period_days=90
            )
            
            # 5. Revenue trends
            revenue_trends = await self.trend_analyzer.predict(
                trend_type="revenue",
                period_days=90
            )
            
            return {
                "success": True,
                "generated_at": datetime.utcnow().isoformat(),
                "tenant_id": self.tenant_id,
                "predictions": {
                    "revenue": {
                        "next_7_days": revenue_7day,
                        "next_30_days": revenue_30day
                    },
                    "bookings": booking_forecast,
                    "churn": churn_analysis,
                    "trends": {
                        "services": service_trends,
                        "revenue": revenue_trends
                    }
                },
                "summary": self._generate_summary(
                    revenue_7day,
                    booking_forecast,
                    churn_analysis,
                    service_trends
                )
            }
            
        except Exception as e:
            self.logger.error(f"Error generating dashboard predictions: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def forecast_revenue(
        self,
        days_ahead: int = 30,
        method: str = "moving_average"
    ) -> Dict[str, Any]:
        """
        Forecast revenue
        
        Args:
            days_ahead: Number of days to forecast
            method: "moving_average" or "prophet"
            
        Returns:
            Revenue forecast
        """
        return await self.revenue_forecaster.predict(
            days_ahead=days_ahead,
            method=method,
            tenant_id=self.tenant_id
        )
    
    async def predict_booking_demand(
        self,
        days_ahead: int = 7,
        include_hourly: bool = False
    ) -> Dict[str, Any]:
        """
        Predict booking demand
        
        Args:
            days_ahead: Number of days to forecast
            include_hourly: Include hourly patterns
            
        Returns:
            Booking demand forecast
        """
        return await self.booking_predictor.predict(
            days_ahead=days_ahead,
            tenant_id=self.tenant_id,
            include_hourly=include_hourly
        )
    
    async def identify_churn_risk(
        self,
        method: str = "rule_based",
        threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        Identify customers at risk of churning
        
        Args:
            method: "rule_based" or "random_forest"
            threshold: Risk threshold (0-1)
            
        Returns:
            Churn risk analysis
        """
        return await self.churn_predictor.predict(
            method=method,
            threshold=threshold,
            tenant_id=self.tenant_id
        )
    
    async def calculate_customer_lifetime_value(
        self,
        customer_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Calculate Customer Lifetime Value
        
        Args:
            customer_id: Optional specific customer ID
            
        Returns:
            CLV calculations
        """
        return await self.churn_predictor.calculate_clv(customer_id)
    
    async def plan_capacity(
        self,
        target_date: date,
        available_staff: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate capacity planning recommendations
        
        Args:
            target_date: Date to plan for
            available_staff: Current staff count
            
        Returns:
            Capacity recommendations
        """
        return await self.capacity_planner.predict(
            target_date=target_date,
            available_staff=available_staff
        )
    
    async def analyze_trends(
        self,
        trend_type: str = "service_popularity",
        period_days: int = 90
    ) -> Dict[str, Any]:
        """
        Analyze business trends
        
        Args:
            trend_type: "service_popularity", "revenue", or "seasonal"
            period_days: Analysis period
            
        Returns:
            Trend analysis
        """
        return await self.trend_analyzer.predict(
            trend_type=trend_type,
            period_days=period_days
        )
    
    async def get_revenue_anomalies(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Detect revenue anomalies
        
        Args:
            days_back: Number of days to analyze
            
        Returns:
            Anomaly detection results
        """
        return await self.revenue_forecaster.get_revenue_anomalies(days_back)
    
    def _generate_summary(
        self,
        revenue: Dict[str, Any],
        bookings: Dict[str, Any],
        churn: Dict[str, Any],
        trends: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate executive summary of predictions
        """
        summary = {
            "key_metrics": {},
            "alerts": [],
            "opportunities": []
        }
        
        # Revenue summary
        if revenue.get('success'):
            total_forecast = revenue.get('summary', {}).get('total_forecast', 0)
            summary['key_metrics']['next_7_days_revenue'] = total_forecast
            
            if total_forecast > 0:
                summary['opportunities'].append(
                    f"💰 Predicted revenue next 7 days: ${total_forecast:,.2f}"
                )
        
        # Booking summary
        if bookings.get('success'):
            daily_forecast = bookings.get('daily_forecast', [])
            if daily_forecast:
                total_bookings = sum(d['predicted_bookings'] for d in daily_forecast)
                summary['key_metrics']['next_7_days_bookings'] = total_bookings
        
        # Churn alerts
        if churn.get('success'):
            high_risk_count = churn.get('high_risk_count', 0)
            if high_risk_count > 0:
                summary['alerts'].append(
                    f"⚠️ {high_risk_count} customers at high risk of churning"
                )
                summary['key_metrics']['customers_at_risk'] = high_risk_count
        
        # Trend insights
        if trends.get('success'):
            trending = trends.get('trends', {})
            if trending.get('growing'):
                top_growing = trending['growing'][0]
                summary['opportunities'].append(
                    f"📈 {top_growing['service_name']} trending up {top_growing['trend_percentage']}%"
                )
        
        return summary

