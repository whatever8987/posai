"""
Capacity Planner - Optimize staff scheduling and resource allocation
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, date
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prediction import PredictionType, ModelType
from .base_predictor import BasePredictor


class CapacityPlanner(BasePredictor):
    """
    Optimize staffing and capacity based on demand predictions
    """
    
    def __init__(self, tenant_schema: str, db: AsyncSession):
        super().__init__(tenant_schema, db)
    
    def get_prediction_type(self) -> PredictionType:
        return PredictionType.CAPACITY
    
    def get_model_type(self) -> ModelType:
        return ModelType.RULE_BASED
    
    async def predict(
        self,
        target_date: date,
        available_staff: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate capacity recommendations for a specific date
        
        Args:
            target_date: Date to optimize
            available_staff: Current staff count (optional)
            
        Returns:
            Capacity optimization recommendations
        """
        try:
            # Get staff performance metrics
            staff_metrics = await self._get_staff_performance()
            
            # Get booking demand for target date
            demand_forecast = await self._forecast_demand_for_date(target_date)
            
            # Calculate optimal staffing
            optimal_staff = await self._calculate_optimal_staffing(
                target_date,
                demand_forecast,
                staff_metrics
            )
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                optimal_staff,
                available_staff,
                demand_forecast
            )
            
            return {
                "success": True,
                "target_date": target_date.isoformat(),
                "demand_forecast": demand_forecast,
                "staff_metrics": staff_metrics,
                "optimal_staffing": optimal_staff,
                "recommendations": recommendations
            }
            
        except Exception as e:
            self.logger.error(f"Error in capacity planning: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _get_staff_performance(self) -> Dict[str, Any]:
        """Get staff performance metrics"""
        query = """
        SELECT 
            s.id,
            s.name,
            COUNT(b.id) as completed_bookings,
            AVG(EXTRACT(EPOCH FROM (b.end_time - b.booking_time)) / 3600) as avg_service_hours,
            SUM(b.total_amount) as total_revenue,
            COUNT(DISTINCT DATE(b.booking_date)) as days_worked
        FROM staff s
        LEFT JOIN bookings b ON s.id = b.technician_id AND b.status = 'completed'
        WHERE b.booking_date >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY s.id, s.name
        HAVING COUNT(b.id) > 0
        """
        
        df = await self.fetch_data(query)
        
        if df.empty:
            return {"staff_count": 0, "avg_productivity": 0}
        
        return {
            "staff_count": len(df),
            "avg_bookings_per_day": round(df['completed_bookings'].sum() / df['days_worked'].sum(), 1),
            "avg_service_hours": round(float(df['avg_service_hours'].mean()), 1),
            "total_revenue": float(df['total_revenue'].sum())
        }
    
    async def _forecast_demand_for_date(self, target_date: date) -> Dict[str, Any]:
        """Forecast booking demand for specific date"""
        dow = target_date.weekday()
        
        query = f"""
        SELECT 
            COUNT(*) as avg_bookings,
            SUM(EXTRACT(EPOCH FROM (end_time - booking_time)) / 3600) as total_hours
        FROM bookings
        WHERE EXTRACT(DOW FROM booking_date) = {dow}
        AND booking_date >= CURRENT_DATE - INTERVAL '60 days'
        AND status = 'completed'
        """
        
        df = await self.fetch_data(query)
        
        if df.empty or df['avg_bookings'].iloc[0] is None:
            return {"predicted_bookings": 0, "predicted_hours": 0}
        
        return {
            "predicted_bookings": int(df['avg_bookings'].iloc[0]),
            "predicted_hours": round(float(df['total_hours'].iloc[0] or 0), 1)
        }
    
    async def _calculate_optimal_staffing(
        self,
        target_date: date,
        demand: Dict[str, Any],
        staff_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate optimal staff count"""
        predicted_hours = demand.get('predicted_hours', 0)
        work_hours_per_staff = 8  # Standard workday
        
        # Account for efficiency (staff typically 75-85% utilized)
        efficiency_factor = 0.8
        effective_hours_per_staff = work_hours_per_staff * efficiency_factor
        
        optimal_count = max(1, int(predicted_hours / effective_hours_per_staff) + 1)
        
        return {
            "optimal_staff_count": optimal_count,
            "predicted_utilization": round((predicted_hours / (optimal_count * work_hours_per_staff)) * 100, 1),
            "buffer_capacity": round((optimal_count * work_hours_per_staff - predicted_hours), 1)
        }
    
    def _generate_recommendations(
        self,
        optimal: Dict[str, Any],
        available: Optional[int],
        demand: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        optimal_count = optimal['optimal_staff_count']
        utilization = optimal['predicted_utilization']
        
        if available:
            if available < optimal_count:
                recommendations.append(
                    f"⚠️ Understaffed: Need {optimal_count} staff, have {available}. "
                    f"Consider adding {optimal_count - available} staff or limiting bookings."
                )
            elif available > optimal_count * 1.5:
                recommendations.append(
                    f"📉 Overstaffed: Need {optimal_count} staff, have {available}. "
                    f"Consider reducing to {optimal_count} or running promotions to increase demand."
                )
            else:
                recommendations.append(
                    f"✅ Optimal staffing: {available} staff is appropriate for predicted demand."
                )
        
        if utilization < 60:
            recommendations.append(
                "💡 Low utilization predicted. Consider promotional offers to fill capacity."
            )
        elif utilization > 90:
            recommendations.append(
                "⚡ High utilization expected. Ensure staff are prepared for busy day."
            )
        
        return recommendations

