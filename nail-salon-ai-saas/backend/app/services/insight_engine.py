"""
Automated Insight Engine
Analyzes salon data and generates actionable business insights
"""
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import asyncio

from ..models import Insight, InsightType, InsightSeverity, InsightStatus


class InsightEngine:
    """
    Generates automated insights by analyzing tenant data
    
    Runs various checks and creates Insight objects for:
    - Low inventory warnings
    - Booking trend changes  
    - Revenue anomalies
    - Customer churn risk
    - Staff performance issues
    - Service popularity shifts
    """
    
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        # Note: Database session should be passed to methods as needed
    
    async def generate_all_insights(self) -> List[Insight]:
        """
        Run all insight checks and return list of new insights
        
        Returns:
            List of Insight objects
        """
        # TODO: Implement database session management for insight generation
        # For now, return empty list to allow backend to start
        return []
        
        # insights = []
        # 
        # # Run all checks in parallel for efficiency
        # checks = [
        #     self.check_low_inventory(),
        #     self.check_booking_trends(),
        #     self.check_revenue_anomalies(),
        #     self.check_customer_churn(),
        #     self.check_peak_hours(),
        #     self.check_staff_performance(),
        #     self.check_no_show_rate(),
        #     self.check_service_popularity()
        # ]
        # 
        # results = await asyncio.gather(*checks, return_exceptions=True)
        # 
        # # Collect all insights, skip errors
        # for result in results:
        #     if isinstance(result, list):
        #         insights.extend(result)
        #     elif isinstance(result, Exception):
        #         # Log error but continue
        #         print(f"Insight check error: {result}")
        # 
        # return insights
    
    async def check_low_inventory(self) -> List[Insight]:
        """
        Check for products running low on stock
        
        Returns insights for products below minimum stock level
        """
        insights = []
        session = await self.tenant_db.get_session()
        
        try:
            query = text("""
                SELECT 
                    product_id,
                    product_name,
                    category,
                    current_stock,
                    min_stock_level,
                    (min_stock_level - current_stock) AS units_short
                FROM products
                WHERE current_stock < min_stock_level
                ORDER BY (min_stock_level - current_stock) DESC
            """)
            
            result = await session.execute(query)
            low_stock_products = result.fetchall()
            
            if low_stock_products:
                # Create insight for each low-stock product
                for product in low_stock_products:
                    severity = self._determine_inventory_severity(
                        product.current_stock,
                        product.min_stock_level
                    )
                    
                    insights.append(Insight(
                        tenant_id=self.tenant_id,
                        type=InsightType.LOW_INVENTORY,
                        severity=severity,
                        title=f"Low Stock Alert: {product.product_name}",
                        description=f"{product.product_name} is running low. Current stock: {product.current_stock}, Minimum level: {product.min_stock_level}",
                        recommendation=f"Reorder {product.units_short} units of {product.product_name} to maintain adequate inventory.",
                        metrics={
                            "current_stock": product.current_stock,
                            "min_stock_level": product.min_stock_level,
                            "units_needed": product.units_short,
                            "category": product.category
                        },
                        affected_entities={"product_id": product.product_id},
                        current_value=float(product.current_stock),
                        previous_value=float(product.min_stock_level),
                        data_source="inventory_check",
                        confidence_score=1.0
                    ))
            
        finally:
            await session.close()
        
        return insights
    
    async def check_booking_trends(self) -> List[Insight]:
        """
        Analyze booking trends for significant changes
        
        Compares current week vs previous 4-week average
        """
        insights = []
        session = await self.tenant_db.get_session()
        
        try:
            query = text("""
                WITH current_week AS (
                    SELECT COUNT(*) as bookings
                    FROM bookings
                    WHERE booking_date >= CURRENT_DATE - INTERVAL '7 days'
                    AND status != 'cancelled'
                ),
                previous_avg AS (
                    SELECT AVG(weekly_count) as avg_bookings
                    FROM (
                        SELECT 
                            DATE_TRUNC('week', booking_date) as week,
                            COUNT(*) as weekly_count
                        FROM bookings
                        WHERE booking_date >= CURRENT_DATE - INTERVAL '35 days'
                        AND booking_date < CURRENT_DATE - INTERVAL '7 days'
                        AND status != 'cancelled'
                        GROUP BY DATE_TRUNC('week', booking_date)
                    ) weeks
                )
                SELECT 
                    cw.bookings as current_bookings,
                    pa.avg_bookings as previous_avg,
                    CASE 
                        WHEN pa.avg_bookings > 0 THEN 
                            ((cw.bookings - pa.avg_bookings) / pa.avg_bookings * 100)
                        ELSE 0
                    END as change_percent
                FROM current_week cw, previous_avg pa
            """)
            
            result = await session.execute(query)
            trend_data = result.fetchone()
            
            if trend_data and trend_data.previous_avg > 0:
                change = trend_data.change_percent
                
                # Only create insight if change is significant (>15%)
                if abs(change) > 15:
                    is_increase = change > 0
                    severity = InsightSeverity.MEDIUM if abs(change) > 25 else InsightSeverity.LOW
                    
                    insights.append(Insight(
                        tenant_id=self.tenant_id,
                        type=InsightType.BOOKING_TREND,
                        severity=severity,
                        title=f"Booking Volume {'Increased' if is_increase else 'Decreased'} by {abs(change):.1f}%",
                        description=f"This week's bookings ({int(trend_data.current_bookings)}) are {abs(change):.1f}% {'higher' if is_increase else 'lower'} than the 4-week average ({int(trend_data.previous_avg)}).",
                        recommendation=self._get_booking_trend_recommendation(is_increase, change),
                        metrics={
                            "current_week_bookings": int(trend_data.current_bookings),
                            "average_bookings": int(trend_data.previous_avg),
                            "change_percent": float(change)
                        },
                        current_value=float(trend_data.current_bookings),
                        previous_value=float(trend_data.previous_avg),
                        change_percent=float(change),
                        data_source="booking_trend_check",
                        confidence_score=0.85
                    ))
        
        finally:
            await session.close()
        
        return insights
    
    async def check_revenue_anomalies(self) -> List[Insight]:
        """
        Detect unusual revenue patterns (spikes or drops)
        
        Analyzes last 7 days vs 30-day average
        """
        insights = []
        session = await self.tenant_db.get_session()
        
        try:
            query = text("""
                WITH recent_revenue AS (
                    SELECT AVG(daily_revenue) as avg_revenue
                    FROM (
                        SELECT 
                            booking_date,
                            SUM(total_amount + tip_amount) as daily_revenue
                        FROM bookings
                        WHERE booking_date >= CURRENT_DATE - INTERVAL '7 days'
                        AND status = 'completed'
                        GROUP BY booking_date
                    ) recent
                ),
                historical_revenue AS (
                    SELECT AVG(daily_revenue) as avg_revenue
                    FROM (
                        SELECT 
                            booking_date,
                            SUM(total_amount + tip_amount) as daily_revenue
                        FROM bookings
                        WHERE booking_date >= CURRENT_DATE - INTERVAL '37 days'
                        AND booking_date < CURRENT_DATE - INTERVAL '7 days'
                        AND status = 'completed'
                        GROUP BY booking_date
                    ) historical
                )
                SELECT 
                    rr.avg_revenue as recent,
                    hr.avg_revenue as historical,
                    CASE 
                        WHEN hr.avg_revenue > 0 THEN
                            ((rr.avg_revenue - hr.avg_revenue) / hr.avg_revenue * 100)
                        ELSE 0
                    END as change_percent
                FROM recent_revenue rr, historical_revenue hr
            """)
            
            result = await session.execute(query)
            revenue_data = result.fetchone()
            
            if revenue_data and revenue_data.historical > 0:
                change = revenue_data.change_percent
                
                # Significant change threshold: 20%
                if abs(change) > 20:
                    is_increase = change > 0
                    severity = InsightSeverity.HIGH if abs(change) > 35 else InsightSeverity.MEDIUM
                    
                    insights.append(Insight(
                        tenant_id=self.tenant_id,
                        type=InsightType.REVENUE_ANOMALY,
                        severity=severity,
                        title=f"Revenue {'Spike' if is_increase else 'Drop'} Detected",
                        description=f"Daily revenue for the past week (${revenue_data.recent:.2f}) is {abs(change):.1f}% {'higher' if is_increase else 'lower'} than the 30-day average (${revenue_data.historical:.2f}).",
                        recommendation=self._get_revenue_anomaly_recommendation(is_increase, change),
                        metrics={
                            "recent_avg_daily": float(revenue_data.recent),
                            "historical_avg_daily": float(revenue_data.historical),
                            "change_percent": float(change)
                        },
                        current_value=float(revenue_data.recent),
                        previous_value=float(revenue_data.historical),
                        change_percent=float(change),
                        data_source="revenue_anomaly_check",
                        confidence_score=0.80
                    ))
        
        finally:
            await session.close()
        
        return insights
    
    async def check_customer_churn(self) -> List[Insight]:
        """
        Identify customers at risk of churning (haven't visited in 60+ days)
        """
        insights = []
        session = await self.tenant_db.get_session()
        
        try:
            query = text("""
                SELECT 
                    c.customer_id,
                    c.first_name || ' ' || c.last_name AS customer_name,
                    c.phone,
                    c.email,
                    MAX(b.booking_date) AS last_visit,
                    CURRENT_DATE - MAX(b.booking_date) AS days_since_visit,
                    COUNT(b.booking_id) AS total_visits,
                    SUM(b.total_amount + b.tip_amount) AS lifetime_value
                FROM customers c
                JOIN bookings b ON c.customer_id = b.customer_id
                WHERE b.status = 'completed'
                GROUP BY c.customer_id, c.first_name, c.last_name, c.phone, c.email
                HAVING CURRENT_DATE - MAX(b.booking_date) BETWEEN 60 AND 120
                ORDER BY lifetime_value DESC
                LIMIT 20
            """)
            
            result = await session.execute(query)
            at_risk_customers = result.fetchall()
            
            if at_risk_customers:
                customer_list = [
                    {
                        "customer_id": c.customer_id,
                        "name": c.customer_name,
                        "phone": c.phone,
                        "last_visit": c.last_visit.isoformat() if c.last_visit else None,
                        "days_since_visit": c.days_since_visit,
                        "lifetime_value": float(c.lifetime_value)
                    }
                    for c in at_risk_customers
                ]
                
                total_value = sum(c.lifetime_value for c in at_risk_customers)
                
                insights.append(Insight(
                    tenant_id=self.tenant_id,
                    type=InsightType.CUSTOMER_CHURN,
                    severity=InsightSeverity.HIGH,
                    title=f"{len(at_risk_customers)} High-Value Customers At Risk",
                    description=f"{len(at_risk_customers)} customers with combined lifetime value of ${total_value:.2f} haven't visited in 60-120 days.",
                    recommendation=f"Launch a win-back campaign targeting these customers. Consider offering a special discount or complimentary service to re-engage them.",
                    metrics={
                        "at_risk_count": len(at_risk_customers),
                        "total_lifetime_value": float(total_value),
                        "avg_days_since_visit": sum(c.days_since_visit for c in at_risk_customers) / len(at_risk_customers)
                    },
                    affected_entities={"customers": customer_list},
                    current_value=float(len(at_risk_customers)),
                    data_source="churn_check",
                    confidence_score=0.90
                ))
        
        finally:
            await session.close()
        
        return insights
    
    async def check_peak_hours(self) -> List[Insight]:
        """
        Analyze booking patterns to identify peak hours
        """
        insights = []
        session = await self.tenant_db.get_session()
        
        try:
            query = text("""
                SELECT 
                    EXTRACT(HOUR FROM booking_time) AS hour,
                    COUNT(*) AS booking_count,
                    AVG(total_amount) AS avg_revenue
                FROM bookings
                WHERE booking_date >= CURRENT_DATE - INTERVAL '30 days'
                AND status IN ('completed', 'scheduled')
                AND booking_time IS NOT NULL
                GROUP BY EXTRACT(HOUR FROM booking_time)
                HAVING COUNT(*) >= 5
                ORDER BY booking_count DESC
                LIMIT 5
            """)
            
            result = await session.execute(query)
            peak_hours = result.fetchall()
            
            if peak_hours:
                top_hour = peak_hours[0]
                
                insights.append(Insight(
                    tenant_id=self.tenant_id,
                    type=InsightType.PEAK_HOURS,
                    severity=InsightSeverity.INFO,
                    title=f"Peak Booking Hour: {int(top_hour.hour)}:00",
                    description=f"The busiest time is around {int(top_hour.hour)}:00 with {top_hour.booking_count} bookings in the past 30 days.",
                    recommendation=f"Ensure adequate staffing around {int(top_hour.hour)}:00. Consider premium pricing during peak hours.",
                    metrics={
                        "peak_hours": [
                            {
                                "hour": int(h.hour),
                                "bookings": h.booking_count,
                                "avg_revenue": float(h.avg_revenue)
                            }
                            for h in peak_hours
                        ]
                    },
                    current_value=float(top_hour.booking_count),
                    data_source="peak_hours_check",
                    confidence_score=0.95
                ))
        
        finally:
            await session.close()
        
        return insights
    
    async def check_staff_performance(self) -> List[Insight]:
        """
        Identify staff performance issues or exceptional performance
        """
        insights = []
        session = await self.tenant_db.get_session()
        
        try:
            query = text("""
                SELECT 
                    t.technician_id,
                    t.first_name || ' ' || t.last_name AS technician_name,
                    COUNT(b.booking_id) AS bookings_this_month,
                    AVG(b.tip_amount) AS avg_tip,
                    SUM(b.total_amount) AS revenue_generated
                FROM technicians t
                LEFT JOIN bookings b ON t.technician_id = b.technician_id
                    AND b.booking_date >= DATE_TRUNC('month', CURRENT_DATE)
                    AND b.status = 'completed'
                WHERE t.is_active = true
                GROUP BY t.technician_id, t.first_name, t.last_name
                HAVING COUNT(b.booking_id) > 0
                ORDER BY avg_tip DESC
            """)
            
            result = await session.execute(query)
            staff_data = result.fetchall()
            
            if len(staff_data) >= 2:
                # Find top performer (by tips, indicator of satisfaction)
                top_performer = staff_data[0]
                
                if top_performer.avg_tip > 0:
                    insights.append(Insight(
                        tenant_id=self.tenant_id,
                        type=InsightType.STAFF_PERFORMANCE,
                        severity=InsightSeverity.INFO,
                        title=f"Top Performer: {top_performer.technician_name}",
                        description=f"{top_performer.technician_name} has the highest customer satisfaction this month with an average tip of ${top_performer.avg_tip:.2f}.",
                        recommendation=f"Consider recognizing {top_performer.technician_name}'s excellent performance. Share their best practices with the team.",
                        metrics={
                            "technician_id": top_performer.technician_id,
                            "bookings": top_performer.bookings_this_month,
                            "avg_tip": float(top_performer.avg_tip),
                            "revenue_generated": float(top_performer.revenue_generated)
                        },
                        affected_entities={"technician_id": top_performer.technician_id},
                        current_value=float(top_performer.avg_tip),
                        data_source="staff_performance_check",
                        confidence_score=0.85
                    ))
        
        finally:
            await session.close()
        
        return insights
    
    async def check_no_show_rate(self) -> List[Insight]:
        """
        Monitor no-show rate for bookings
        """
        insights = []
        session = await self.tenant_db.get_session()
        
        try:
            query = text("""
                SELECT 
                    COUNT(*) FILTER (WHERE status = 'no_show') AS no_shows,
                    COUNT(*) AS total_bookings,
                    CASE 
                        WHEN COUNT(*) > 0 THEN 
                            (COUNT(*) FILTER (WHERE status = 'no_show')::float / COUNT(*) * 100)
                        ELSE 0
                    END AS no_show_rate,
                    SUM(CASE WHEN status = 'no_show' THEN total_amount ELSE 0 END) AS lost_revenue
                FROM bookings
                WHERE booking_date >= CURRENT_DATE - INTERVAL '30 days'
            """)
            
            result = await session.execute(query)
            no_show_data = result.fetchone()
            
            if no_show_data and no_show_data.no_show_rate > 10:  # Alert if >10%
                severity = InsightSeverity.HIGH if no_show_data.no_show_rate > 20 else InsightSeverity.MEDIUM
                
                insights.append(Insight(
                    tenant_id=self.tenant_id,
                    type=InsightType.NO_SHOW_RATE,
                    severity=severity,
                    title=f"High No-Show Rate: {no_show_data.no_show_rate:.1f}%",
                    description=f"{no_show_data.no_shows} no-shows out of {no_show_data.total_bookings} bookings in the past 30 days ({no_show_data.no_show_rate:.1f}%), resulting in ${no_show_data.lost_revenue:.2f} in lost revenue.",
                    recommendation="Consider implementing a deposit policy, sending reminder texts/emails, or creating a cancellation fee to reduce no-shows.",
                    metrics={
                        "no_shows": no_show_data.no_shows,
                        "total_bookings": no_show_data.total_bookings,
                        "no_show_rate": float(no_show_data.no_show_rate),
                        "lost_revenue": float(no_show_data.lost_revenue)
                    },
                    current_value=float(no_show_data.no_show_rate),
                    data_source="no_show_check",
                    confidence_score=0.95
                ))
        
        finally:
            await session.close()
        
        return insights
    
    async def check_service_popularity(self) -> List[Insight]:
        """
        Track changes in service popularity
        """
        insights = []
        session = await self.tenant_db.get_session()
        
        try:
            query = text("""
                WITH current_period AS (
                    SELECT 
                        s.service_id,
                        s.service_name,
                        COUNT(*) as bookings
                    FROM services s
                    JOIN booking_services bs ON s.service_id = bs.service_id
                    JOIN bookings b ON bs.booking_id = b.booking_id
                    WHERE b.booking_date >= CURRENT_DATE - INTERVAL '14 days'
                    AND b.status = 'completed'
                    GROUP BY s.service_id, s.service_name
                    ORDER BY bookings DESC
                    LIMIT 1
                )
                SELECT * FROM current_period
            """)
            
            result = await session.execute(query)
            top_service = result.fetchone()
            
            if top_service:
                insights.append(Insight(
                    tenant_id=self.tenant_id,
                    type=InsightType.SERVICE_POPULARITY,
                    severity=InsightSeverity.INFO,
                    title=f"Trending Service: {top_service.service_name}",
                    description=f"{top_service.service_name} is the most popular service with {top_service.bookings} bookings in the past 2 weeks.",
                    recommendation=f"Consider promoting {top_service.service_name} more heavily or training additional staff on this service.",
                    metrics={
                        "service_id": top_service.service_id,
                        "service_name": top_service.service_name,
                        "bookings": top_service.bookings
                    },
                    affected_entities={"service_id": top_service.service_id},
                    current_value=float(top_service.bookings),
                    data_source="service_popularity_check",
                    confidence_score=0.90
                ))
        
        finally:
            await session.close()
        
        return insights
    
    # Helper methods
    
    def _determine_inventory_severity(self, current_stock: int, min_level: int) -> InsightSeverity:
        """Determine severity based on how low stock is"""
        if current_stock == 0:
            return InsightSeverity.CRITICAL
        elif current_stock <= min_level * 0.25:
            return InsightSeverity.HIGH
        elif current_stock <= min_level * 0.50:
            return InsightSeverity.MEDIUM
        else:
            return InsightSeverity.LOW
    
    def _get_booking_trend_recommendation(self, is_increase: bool, change_percent: float) -> str:
        """Generate recommendation based on booking trend"""
        if is_increase:
            if change_percent > 30:
                return "Significant increase in demand. Consider adding staff hours and managing capacity to maintain service quality."
            else:
                return "Positive booking trend. Monitor capacity and consider promotional campaigns to sustain momentum."
        else:
            if change_percent < -30:
                return "Significant drop in bookings. Review recent changes, launch promotional campaigns, and reach out to inactive customers."
            else:
                return "Slight decrease in bookings. Consider targeted marketing campaigns or special offers to boost volume."
    
    def _get_revenue_anomaly_recommendation(self, is_increase: bool, change_percent: float) -> str:
        """Generate recommendation based on revenue anomaly"""
        if is_increase:
            return "Revenue is significantly higher than usual. Investigate the cause (new service, marketing campaign, seasonal?) to replicate success."
        else:
            return "Revenue has dropped significantly. Review pricing, service quality, and competitor activity. Consider win-back campaigns for inactive customers."

