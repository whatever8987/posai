"""
Booking Demand Predictor - Forecast appointment volume and patterns

Predicts:
- Total bookings per day
- Bookings by service type
- Peak hours identification
- Capacity utilization
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, date
import pandas as pd
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prediction import PredictionType, ModelType
from .base_predictor import BasePredictor


class BookingPredictor(BasePredictor):
    """
    Predict booking demand to optimize staffing and capacity
    """
    
    def __init__(self, tenant_schema: str, db: AsyncSession):
        super().__init__(tenant_schema, db)
    
    def get_prediction_type(self) -> PredictionType:
        return PredictionType.BOOKING_DEMAND
    
    def get_model_type(self) -> ModelType:
        return ModelType.MOVING_AVERAGE
    
    async def predict(
        self,
        days_ahead: int = 7,
        tenant_id: Optional[int] = None,
        include_hourly: bool = False
    ) -> Dict[str, Any]:
        """
        Predict booking demand
        
        Args:
            days_ahead: Number of days to forecast
            tenant_id: Tenant ID for saving predictions
            include_hourly: Include hourly breakdown
            
        Returns:
            Dict with demand forecast
        """
        try:
            # Get daily booking patterns
            daily_forecast = await self._forecast_daily_bookings(days_ahead, tenant_id)
            
            # Get service type breakdown
            service_forecast = await self._forecast_by_service_type(days_ahead)
            
            # Get hourly patterns if requested
            hourly_patterns = None
            if include_hourly:
                hourly_patterns = await self._get_hourly_patterns()
            
            return {
                "success": True,
                "forecast_days": days_ahead,
                "daily_forecast": daily_forecast,
                "service_forecast": service_forecast,
                "hourly_patterns": hourly_patterns,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in booking prediction: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "daily_forecast": []
            }
    
    async def _forecast_daily_bookings(
        self,
        days_ahead: int,
        tenant_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Forecast daily booking volume using historical patterns
        """
        # Fetch historical booking counts by day
        query = """
        WITH daily_bookings AS (
            SELECT 
                DATE(booking_date) as date,
                COUNT(*) as booking_count,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_count,
                COUNT(CASE WHEN status = 'cancelled' THEN 1 END) as cancelled_count
            FROM bookings
            WHERE booking_date >= CURRENT_DATE - INTERVAL '60 days'
            GROUP BY DATE(booking_date)
            ORDER BY date
        )
        SELECT 
            date,
            booking_count,
            completed_count,
            cancelled_count,
            EXTRACT(DOW FROM date) as day_of_week
        FROM daily_bookings
        """
        
        df = await self.fetch_data(query)
        
        if df.empty:
            return []
        
        # Calculate day-of-week averages
        dow_avg = df.groupby('day_of_week')['booking_count'].mean().to_dict()
        overall_avg = df['booking_count'].mean()
        
        # Calculate completion rate
        completion_rate = df['completed_count'].sum() / df['booking_count'].sum()
        
        # Generate forecast
        last_date = pd.to_datetime(df['date'].iloc[-1])
        forecast = []
        
        for i in range(1, days_ahead + 1):
            forecast_date = last_date + timedelta(days=i)
            dow = forecast_date.dayofweek
            
            # Predict based on day-of-week pattern
            predicted_bookings = int(dow_avg.get(dow, overall_avg))
            predicted_completed = int(predicted_bookings * completion_rate)
            
            # Confidence interval (±15% for booking predictions)
            lower = int(predicted_bookings * 0.85)
            upper = int(predicted_bookings * 1.15)
            
            forecast_item = {
                "date": forecast_date.strftime("%Y-%m-%d"),
                "day_of_week": forecast_date.strftime("%A"),
                "predicted_bookings": predicted_bookings,
                "predicted_completed": predicted_completed,
                "lower_bound": lower,
                "upper_bound": upper,
                "confidence": 0.80
            }
            
            forecast.append(forecast_item)
            
            # Save prediction if tenant_id provided
            if tenant_id:
                await self.save_prediction(
                    tenant_id=tenant_id,
                    predicted_value={
                        "bookings": predicted_bookings,
                        "completed": predicted_completed
                    },
                    confidence_interval={
                        "lower": lower,
                        "upper": upper
                    },
                    confidence_score=0.80,
                    target_date=forecast_date.date(),
                    metadata={
                        "method": "day_of_week_average",
                        "completion_rate": round(completion_rate, 2)
                    },
                    valid_until=datetime.utcnow() + timedelta(days=7)
                )
        
        return forecast
    
    async def _forecast_by_service_type(self, days_ahead: int) -> Dict[str, Any]:
        """
        Predict demand by service category
        """
        query = """
        WITH service_stats AS (
            SELECT 
                s.category,
                COUNT(bs.id) as booking_count,
                COUNT(bs.id) * 1.0 / (
                    SELECT COUNT(*) 
                    FROM booking_services bs2
                    JOIN bookings b2 ON bs2.booking_id = b2.id
                    WHERE b2.booking_date >= CURRENT_DATE - INTERVAL '30 days'
                ) as popularity_ratio
            FROM booking_services bs
            JOIN bookings b ON bs.booking_id = b.id
            JOIN services s ON bs.service_id = s.id
            WHERE b.booking_date >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY s.category
        )
        SELECT 
            category,
            booking_count,
            ROUND(popularity_ratio::numeric, 3) as popularity_ratio
        FROM service_stats
        ORDER BY booking_count DESC
        """
        
        df = await self.fetch_data(query)
        
        if df.empty:
            return {}
        
        # Calculate expected bookings per category
        service_forecast = {}
        for _, row in df.iterrows():
            category = row['category']
            service_forecast[category] = {
                "historical_monthly": int(row['booking_count']),
                "popularity_ratio": float(row['popularity_ratio']),
                "forecast_next_period": int(row['booking_count'] * (days_ahead / 30))
            }
        
        return service_forecast
    
    async def _get_hourly_patterns(self) -> Dict[str, Any]:
        """
        Analyze hourly booking patterns to identify peak times
        """
        query = """
        SELECT 
            EXTRACT(HOUR FROM booking_time) as hour,
            EXTRACT(DOW FROM booking_date) as day_of_week,
            COUNT(*) as booking_count,
            AVG(total_amount) as avg_value
        FROM bookings
        WHERE booking_date >= CURRENT_DATE - INTERVAL '30 days'
        AND status != 'cancelled'
        GROUP BY hour, day_of_week
        ORDER BY day_of_week, hour
        """
        
        df = await self.fetch_data(query)
        
        if df.empty:
            return {}
        
        # Group by hour across all days
        hourly_avg = df.groupby('hour').agg({
            'booking_count': 'mean',
            'avg_value': 'mean'
        }).round(2)
        
        # Identify peak hours (>80th percentile)
        threshold = hourly_avg['booking_count'].quantile(0.8)
        peak_hours = hourly_avg[hourly_avg['booking_count'] >= threshold].index.tolist()
        
        # Identify slow hours (<20th percentile)
        slow_threshold = hourly_avg['booking_count'].quantile(0.2)
        slow_hours = hourly_avg[hourly_avg['booking_count'] <= slow_threshold].index.tolist()
        
        return {
            "peak_hours": [int(h) for h in peak_hours],
            "slow_hours": [int(h) for h in slow_hours],
            "hourly_averages": {
                int(hour): {
                    "avg_bookings": float(row['booking_count']),
                    "avg_revenue": float(row['avg_value'])
                }
                for hour, row in hourly_avg.iterrows()
            }
        }
    
    async def predict_capacity_utilization(
        self,
        target_date: date,
        available_staff: int
    ) -> Dict[str, Any]:
        """
        Predict capacity utilization for staffing optimization
        
        Args:
            target_date: Date to predict
            available_staff: Number of staff members available
            
        Returns:
            Capacity utilization forecast
        """
        try:
            # Get predicted bookings for that day
            dow = target_date.weekday()
            
            query = f"""
            WITH booking_stats AS (
                SELECT 
                    COUNT(*) as booking_count,
                    AVG(EXTRACT(EPOCH FROM (end_time - booking_time)) / 3600) as avg_duration_hours
                FROM bookings
                WHERE EXTRACT(DOW FROM booking_date) = {dow}
                AND booking_date >= CURRENT_DATE - INTERVAL '60 days'
                AND status = 'completed'
            )
            SELECT 
                ROUND(AVG(booking_count)) as avg_bookings,
                ROUND(AVG(avg_duration_hours)::numeric, 1) as avg_duration
            FROM booking_stats
            """
            
            df = await self.fetch_data(query)
            
            if df.empty or df['avg_bookings'].iloc[0] is None:
                return {
                    "success": False,
                    "error": "Insufficient data for capacity prediction"
                }
            
            avg_bookings = float(df['avg_bookings'].iloc[0])
            avg_duration = float(df['avg_duration'].iloc[0] or 1.0)
            
            # Assume 8-hour workday
            total_staff_hours = available_staff * 8
            predicted_needed_hours = avg_bookings * avg_duration
            utilization = (predicted_needed_hours / total_staff_hours) * 100
            
            # Determine recommendation
            if utilization < 50:
                recommendation = "Overstaffed - Consider reducing staff or running promotions"
            elif utilization > 85:
                recommendation = "Understaffed - Consider adding staff or limiting bookings"
            else:
                recommendation = "Optimal staffing level"
            
            return {
                "success": True,
                "date": target_date.isoformat(),
                "predicted_bookings": int(avg_bookings),
                "avg_service_duration_hours": avg_duration,
                "available_staff": available_staff,
                "total_staff_hours": total_staff_hours,
                "predicted_needed_hours": round(predicted_needed_hours, 1),
                "utilization_percentage": round(utilization, 1),
                "recommendation": recommendation
            }
            
        except Exception as e:
            self.logger.error(f"Error predicting capacity: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

