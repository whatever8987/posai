"""
Trend Analyzer - Identify and analyze business trends

Analyzes:
- Service popularity trends
- Revenue trends
- Customer behavior patterns
- Seasonal patterns
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, date
import pandas as pd
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prediction import PredictionType, ModelType
from .base_predictor import BasePredictor


class TrendAnalyzer(BasePredictor):
    """
    Analyze trends in services, revenue, and customer behavior
    """
    
    def __init__(self, tenant_schema: str, db: AsyncSession):
        super().__init__(tenant_schema, db)
    
    def get_prediction_type(self) -> PredictionType:
        return PredictionType.SERVICE_TREND
    
    def get_model_type(self) -> ModelType:
        return ModelType.LINEAR_REGRESSION
    
    async def predict(
        self,
        trend_type: str = "service_popularity",
        period_days: int = 90
    ) -> Dict[str, Any]:
        """
        Analyze trends
        
        Args:
            trend_type: Type of trend to analyze
            period_days: Analysis period in days
            
        Returns:
            Trend analysis results
        """
        if trend_type == "service_popularity":
            return await self._analyze_service_trends(period_days)
        elif trend_type == "revenue":
            return await self._analyze_revenue_trends(period_days)
        elif trend_type == "seasonal":
            return await self._analyze_seasonal_patterns()
        else:
            raise ValueError(f"Unknown trend type: {trend_type}")
    
    async def _analyze_service_trends(self, period_days: int) -> Dict[str, Any]:
        """
        Analyze service popularity trends
        Identify growing, declining, and stable services
        """
        try:
            # Get service booking counts over time
            query = f"""
            WITH service_monthly AS (
                SELECT 
                    s.id as service_id,
                    s.name as service_name,
                    s.category,
                    DATE_TRUNC('month', b.booking_date) as month,
                    COUNT(bs.id) as booking_count,
                    SUM(s.base_price) as revenue
                FROM services s
                JOIN booking_services bs ON s.id = bs.service_id
                JOIN bookings b ON bs.booking_id = b.id
                WHERE b.booking_date >= CURRENT_DATE - INTERVAL '{period_days} days'
                AND b.status = 'completed'
                GROUP BY s.id, s.name, s.category, DATE_TRUNC('month', b.booking_date)
            )
            SELECT 
                service_id,
                service_name,
                category,
                month,
                booking_count,
                revenue
            FROM service_monthly
            ORDER BY service_id, month
            """
            
            df = await self.fetch_data(query)
            
            if df.empty:
                return {
                    "success": False,
                    "error": "No service data available",
                    "trends": []
                }
            
            # Calculate trends for each service
            service_trends = []
            
            for service_id in df['service_id'].unique():
                service_df = df[df['service_id'] == service_id].sort_values('month')
                
                if len(service_df) < 2:
                    continue
                
                service_name = service_df['service_name'].iloc[0]
                category = service_df['category'].iloc[0]
                
                # Calculate trend using linear regression
                x = np.arange(len(service_df))
                y = service_df['booking_count'].values
                
                # Simple linear regression
                if len(x) > 1:
                    slope, intercept = np.polyfit(x, y, 1)
                    
                    # Calculate trend percentage
                    if y[0] > 0:
                        trend_pct = (slope / y[0]) * 100
                    else:
                        trend_pct = 0
                    
                    # Classify trend
                    if trend_pct > 10:
                        trend_direction = "growing"
                        emoji = "📈"
                    elif trend_pct < -10:
                        trend_direction = "declining"
                        emoji = "📉"
                    else:
                        trend_direction = "stable"
                        emoji = "➡️"
                    
                    service_trends.append({
                        "service_id": int(service_id),
                        "service_name": service_name,
                        "category": category,
                        "trend_direction": trend_direction,
                        "trend_percentage": round(trend_pct, 1),
                        "current_monthly_bookings": int(y[-1]),
                        "previous_monthly_bookings": int(y[0]),
                        "total_revenue": float(service_df['revenue'].sum()),
                        "trend_indicator": emoji
                    })
            
            # Sort by trend strength
            service_trends.sort(key=lambda x: abs(x['trend_percentage']), reverse=True)
            
            # Categorize trends
            growing = [t for t in service_trends if t['trend_direction'] == 'growing']
            declining = [t for t in service_trends if t['trend_direction'] == 'declining']
            stable = [t for t in service_trends if t['trend_direction'] == 'stable']
            
            return {
                "success": True,
                "period_days": period_days,
                "total_services_analyzed": len(service_trends),
                "trends": {
                    "growing": growing[:10],  # Top 10
                    "declining": declining[:10],
                    "stable": stable[:5]
                },
                "summary": {
                    "growing_count": len(growing),
                    "declining_count": len(declining),
                    "stable_count": len(stable)
                },
                "insights": self._generate_service_insights(growing, declining)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing service trends: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "trends": []
            }
    
    async def _analyze_revenue_trends(self, period_days: int) -> Dict[str, Any]:
        """
        Analyze revenue trends and patterns
        """
        try:
            query = f"""
            WITH daily_revenue AS (
                SELECT 
                    DATE(booking_date) as date,
                    SUM(total_amount) as revenue,
                    COUNT(*) as bookings,
                    AVG(total_amount) as avg_ticket
                FROM bookings
                WHERE booking_date >= CURRENT_DATE - INTERVAL '{period_days} days'
                AND status = 'completed'
                GROUP BY DATE(booking_date)
                ORDER BY date
            )
            SELECT 
                date,
                revenue,
                bookings,
                avg_ticket,
                AVG(revenue) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as revenue_7day_ma
            FROM daily_revenue
            """
            
            df = await self.fetch_data(query)
            
            if df.empty:
                return {
                    "success": False,
                    "error": "No revenue data available"
                }
            
            # Calculate overall trend
            x = np.arange(len(df))
            y = df['revenue'].values
            
            slope, intercept = np.polyfit(x, y, 1)
            trend_pct = (slope / y[0]) * 100 if y[0] > 0 else 0
            
            # Identify best and worst days
            best_day = df.loc[df['revenue'].idxmax()]
            worst_day = df.loc[df['revenue'].idxmin()]
            
            # Calculate growth rate
            first_week_avg = df['revenue'].head(7).mean()
            last_week_avg = df['revenue'].tail(7).mean()
            growth_rate = ((last_week_avg - first_week_avg) / first_week_avg * 100) if first_week_avg > 0 else 0
            
            return {
                "success": True,
                "period_days": period_days,
                "trend_direction": "growing" if trend_pct > 5 else "declining" if trend_pct < -5 else "stable",
                "trend_percentage": round(trend_pct, 1),
                "week_over_week_growth": round(growth_rate, 1),
                "summary": {
                    "total_revenue": round(float(df['revenue'].sum()), 2),
                    "avg_daily_revenue": round(float(df['revenue'].mean()), 2),
                    "avg_ticket_value": round(float(df['avg_ticket'].mean()), 2),
                    "total_bookings": int(df['bookings'].sum())
                },
                "best_day": {
                    "date": str(best_day['date']),
                    "revenue": float(best_day['revenue']),
                    "bookings": int(best_day['bookings'])
                },
                "worst_day": {
                    "date": str(worst_day['date']),
                    "revenue": float(worst_day['revenue']),
                    "bookings": int(worst_day['bookings'])
                },
                "insights": self._generate_revenue_insights(trend_pct, growth_rate)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing revenue trends: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _analyze_seasonal_patterns(self) -> Dict[str, Any]:
        """
        Identify seasonal patterns in bookings and revenue
        """
        try:
            query = """
            SELECT 
                EXTRACT(MONTH FROM booking_date) as month,
                EXTRACT(DOW FROM booking_date) as day_of_week,
                COUNT(*) as booking_count,
                SUM(total_amount) as revenue
            FROM bookings
            WHERE booking_date >= CURRENT_DATE - INTERVAL '365 days'
            AND status = 'completed'
            GROUP BY EXTRACT(MONTH FROM booking_date), EXTRACT(DOW FROM booking_date)
            ORDER BY month, day_of_week
            """
            
            df = await self.fetch_data(query)
            
            if df.empty:
                return {
                    "success": False,
                    "error": "Insufficient data for seasonal analysis"
                }
            
            # Monthly patterns
            monthly = df.groupby('month').agg({
                'booking_count': 'sum',
                'revenue': 'sum'
            }).reset_index()
            
            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            monthly_patterns = []
            
            for _, row in monthly.iterrows():
                month_idx = int(row['month']) - 1
                monthly_patterns.append({
                    "month": month_names[month_idx],
                    "bookings": int(row['booking_count']),
                    "revenue": float(row['revenue'])
                })
            
            # Day of week patterns
            dow_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            weekly = df.groupby('day_of_week').agg({
                'booking_count': 'mean',
                'revenue': 'mean'
            }).reset_index()
            
            weekly_patterns = []
            for _, row in weekly.iterrows():
                dow_idx = int(row['day_of_week'])
                weekly_patterns.append({
                    "day": dow_names[dow_idx],
                    "avg_bookings": round(float(row['booking_count']), 1),
                    "avg_revenue": round(float(row['revenue']), 2)
                })
            
            # Identify peak periods
            peak_month = monthly.loc[monthly['revenue'].idxmax()]
            peak_day = weekly.loc[weekly['revenue'].idxmax()]
            
            return {
                "success": True,
                "monthly_patterns": monthly_patterns,
                "weekly_patterns": weekly_patterns,
                "peak_periods": {
                    "peak_month": month_names[int(peak_month['month']) - 1],
                    "peak_day": dow_names[int(peak_day['day_of_week'])]
                },
                "insights": self._generate_seasonal_insights(monthly_patterns, weekly_patterns)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing seasonal patterns: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_service_insights(self, growing: List, declining: List) -> List[str]:
        """Generate insights from service trends"""
        insights = []
        
        if growing:
            top_growing = growing[0]
            insights.append(
                f"🌟 {top_growing['service_name']} is trending up {top_growing['trend_percentage']}% - "
                "consider highlighting in promotions"
            )
        
        if declining:
            top_declining = declining[0]
            insights.append(
                f"⚠️ {top_declining['service_name']} declining {abs(top_declining['trend_percentage'])}% - "
                "may need promotional support or menu refresh"
            )
        
        return insights
    
    def _generate_revenue_insights(self, trend_pct: float, growth_rate: float) -> List[str]:
        """Generate insights from revenue trends"""
        insights = []
        
        if trend_pct > 10:
            insights.append(f"📈 Strong revenue growth trend (+{trend_pct:.1f}%) - business is thriving!")
        elif trend_pct < -10:
            insights.append(f"📉 Revenue declining ({trend_pct:.1f}%) - consider marketing initiatives")
        
        if growth_rate > 20:
            insights.append(f"🚀 Week-over-week revenue up {growth_rate:.1f}% - momentum building!")
        elif growth_rate < -20:
            insights.append(f"⚠️ Week-over-week revenue down {growth_rate:.1f}% - needs attention")
        
        return insights
    
    def _generate_seasonal_insights(self, monthly: List, weekly: List) -> List[str]:
        """Generate insights from seasonal patterns"""
        insights = []
        
        # Find busiest day
        busiest_day = max(weekly, key=lambda x: x['avg_revenue'])
        insights.append(f"📅 {busiest_day['day']} is your busiest day - ensure adequate staffing")
        
        # Find slowest day
        slowest_day = min(weekly, key=lambda x: x['avg_revenue'])
        insights.append(f"💡 {slowest_day['day']} has lowest demand - perfect for promotions")
        
        return insights

