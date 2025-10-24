"""
Recommendation Engine - Phase 5: AI-Powered Business Recommendations

Generates actionable recommendations based on predictions, insights, and business data
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, date
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.models.recommendation import (
    Recommendation,
    RecommendationType,
    RecommendationPriority,
    RecommendationStatus
)
from app.services.forecasting import ForecastingService

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    Main recommendation engine that generates AI-powered business recommendations
    
    Uses predictions from Phase 4 to generate actionable insights for:
    - Promotions (based on trends + capacity)
    - Scheduling (based on demand forecasts)
    - Retention (based on churn predictions)
    - Inventory (based on usage rates)
    - Pricing (based on demand elasticity)
    """
    
    def __init__(self, tenant_schema: str, db: AsyncSession, tenant_id: int):
        self.tenant_schema = tenant_schema
        self.db = db
        self.tenant_id = tenant_id
        self.forecasting = ForecastingService(tenant_schema, db, tenant_id)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def generate_all_recommendations(self) -> Dict[str, Any]:
        """
        Generate all types of recommendations
        
        Returns comprehensive recommendations across all categories
        """
        try:
            self.logger.info(f"Generating recommendations for tenant {self.tenant_id}")
            
            recommendations = {
                "promotion": await self.generate_promotion_recommendations(),
                "scheduling": await self.generate_scheduling_recommendations(),
                "retention": await self.generate_retention_recommendations(),
                "inventory": await self.generate_inventory_recommendations(),
                "pricing": await self.generate_pricing_recommendations()
            }
            
            # Calculate summary
            total_count = sum(len(recs) for recs in recommendations.values())
            critical_count = sum(
                len([r for r in recs if r.get('priority') == 'critical'])
                for recs in recommendations.values()
            )
            
            return {
                "success": True,
                "tenant_id": self.tenant_id,
                "generated_at": datetime.utcnow().isoformat(),
                "recommendations": recommendations,
                "summary": {
                    "total_recommendations": total_count,
                    "critical_priority": critical_count,
                    "by_type": {
                        rec_type: len(recs)
                        for rec_type, recs in recommendations.items()
                    }
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "recommendations": {}
            }
    
    async def generate_promotion_recommendations(self) -> List[Dict[str, Any]]:
        """
        Generate promotion recommendations based on:
        - Service trends (promote growing services)
        - Capacity gaps (fill slow periods)
        - Seasonal patterns
        """
        recommendations = []
        
        try:
            # Get service trends
            trends = await self.forecasting.analyze_trends(
                trend_type="service_popularity",
                period_days=90
            )
            
            # Get capacity data
            booking_forecast = await self.forecasting.predict_booking_demand(days_ahead=7)
            
            # Recommendation 1: Promote trending services
            if trends.get('success') and trends.get('trends', {}).get('growing'):
                growing_services = trends['trends']['growing'][:3]  # Top 3
                for service in growing_services:
                    recommendations.append({
                        "type": "promotion",
                        "priority": "medium",
                        "title": f"Capitalize on {service['service_name']} trend",
                        "description": f"{service['service_name']} bookings are up {service['trend_percentage']}%. "
                                     f"Consider featuring it in marketing to maximize momentum.",
                        "reasoning": {
                            "trend_percentage": service['trend_percentage'],
                            "current_bookings": service['current_monthly_bookings'],
                            "category": service['category']
                        },
                        "action_items": [
                            f"Feature {service['service_name']} in social media posts",
                            "Add to homepage banner",
                            "Train staff on upselling opportunities",
                            "Consider bundle deals with complementary services"
                        ],
                        "expected_impact": {
                            "revenue_increase": "10-15%",
                            "booking_increase": f"{int(service['trend_percentage'] * 0.5)} additional monthly bookings"
                        },
                        "confidence_score": 0.8
                    })
            
            # Recommendation 2: Fill capacity gaps
            if booking_forecast.get('success') and booking_forecast.get('hourly_patterns'):
                slow_hours = booking_forecast['hourly_patterns'].get('slow_hours', [])
                if slow_hours:
                    slow_times = ', '.join([f"{h}:00" for h in slow_hours[:3]])
                    recommendations.append({
                        "type": "promotion",
                        "priority": "high",
                        "title": "Fill slow time slots with targeted promotions",
                        "description": f"Your salon has low utilization during {slow_times}. "
                                     f"Run time-specific promotions to increase capacity usage.",
                        "reasoning": {
                            "slow_hours": slow_hours,
                            "utilization_rate": "<40%",
                            "opportunity": "20-30% revenue increase in these slots"
                        },
                        "action_items": [
                            f"Offer 15-20% discount for appointments at {slow_times}",
                            "Create 'Happy Hour' promotion campaign",
                            "Target customers with flexible schedules",
                            "Promote on social media day-before"
                        ],
                        "expected_impact": {
                            "additional_revenue": "$800-1,200/week",
                            "utilization_increase": "20-30%",
                            "new_customers": "5-8 per week"
                        },
                        "confidence_score": 0.85
                    })
            
            # Recommendation 3: Seasonal promotions
            seasonal_analysis = await self.forecasting.analyze_trends(
                trend_type="seasonal",
                period_days=365
            )
            if seasonal_analysis.get('success'):
                recommendations.append({
                    "type": "promotion",
                    "priority": "medium",
                    "title": "Prepare seasonal promotion campaign",
                    "description": "Based on historical patterns, plan seasonal promotions to match customer demand cycles.",
                    "reasoning": {
                        "peak_month": seasonal_analysis.get('peak_periods', {}).get('peak_month'),
                        "peak_day": seasonal_analysis.get('peak_periods', {}).get('peak_day'),
                        "data_source": "12-month historical analysis"
                    },
                    "action_items": [
                        "Plan holiday-themed service packages",
                        "Create gift certificate promotion",
                        "Prepare inventory for peak season",
                        "Schedule extra staff for busy periods"
                    ],
                    "expected_impact": {
                        "revenue_increase": "15-20% during peak season",
                        "customer_acquisition": "10-15 new customers"
                    },
                    "confidence_score": 0.75
                })
            
        except Exception as e:
            self.logger.error(f"Error generating promotion recommendations: {str(e)}")
        
        return recommendations
    
    async def generate_scheduling_recommendations(self) -> List[Dict[str, Any]]:
        """
        Generate scheduling recommendations based on:
        - Booking demand forecasts
        - Staff capacity planning
        - Peak hour identification
        """
        recommendations = []
        
        try:
            # Get booking forecast for next 7 days
            booking_forecast = await self.forecasting.predict_booking_demand(
                days_ahead=7,
                include_hourly=True
            )
            
            if not booking_forecast.get('success'):
                return recommendations
            
            daily_forecast = booking_forecast.get('daily_forecast', [])
            
            # Recommendation 1: Identify high-demand days
            high_demand_days = [
                day for day in daily_forecast
                if day['predicted_bookings'] > day.get('upper_bound', float('inf')) * 0.8
            ]
            
            if high_demand_days:
                day = high_demand_days[0]
                recommendations.append({
                    "type": "scheduling",
                    "priority": "high",
                    "title": f"Add staff for high-demand {day['day_of_week']}",
                    "description": f"Predicted {day['predicted_bookings']} bookings on {day['date']} "
                                 f"({day['day_of_week']}). Ensure adequate staffing to handle demand.",
                    "reasoning": {
                        "predicted_bookings": day['predicted_bookings'],
                        "typical_range": f"{day.get('lower_bound', 0)}-{day.get('upper_bound', 0)}",
                        "confidence": day['confidence']
                    },
                    "action_items": [
                        f"Schedule +2 additional technicians for {day['date']}",
                        "Prepare backup staff on-call",
                        "Stock extra supplies for high volume",
                        "Consider extending hours if possible"
                    ],
                    "expected_impact": {
                        "service_quality": "Maintained despite high volume",
                        "wait_time_reduction": "30-40%",
                        "revenue_opportunity": f"${day['predicted_bookings'] * 45}"
                    },
                    "confidence_score": day['confidence']
                })
            
            # Recommendation 2: Optimize for low-demand days
            low_demand_days = [
                day for day in daily_forecast
                if day['predicted_bookings'] < day.get('lower_bound', 0) * 1.2
            ]
            
            if low_demand_days:
                day = low_demand_days[0]
                recommendations.append({
                    "type": "scheduling",
                    "priority": "medium",
                    "title": f"Reduce staffing on slow {day['day_of_week']}",
                    "description": f"Only {day['predicted_bookings']} bookings expected on {day['date']}. "
                                 f"Optimize staff schedule to reduce labor costs.",
                    "reasoning": {
                        "predicted_bookings": day['predicted_bookings'],
                        "typical_staffing": "5-6 technicians",
                        "optimal_staffing": "3-4 technicians"
                    },
                    "action_items": [
                        f"Reduce to 3-4 technicians on {day['date']}",
                        "Schedule training or deep cleaning tasks",
                        "Offer split shifts to reduce hours",
                        "Consider running promotion to increase bookings"
                    ],
                    "expected_impact": {
                        "labor_cost_savings": "$200-300",
                        "utilization_improvement": "15-20%",
                        "staff_efficiency": "Improved"
                    },
                    "confidence_score": day['confidence']
                })
            
            # Recommendation 3: Peak hours staffing
            hourly_patterns = booking_forecast.get('hourly_patterns', {})
            peak_hours = hourly_patterns.get('peak_hours', [])
            
            if peak_hours:
                peak_times = ', '.join([f"{h}:00-{h+1}:00" for h in peak_hours[:3]])
                recommendations.append({
                    "type": "scheduling",
                    "priority": "medium",
                    "title": "Optimize staff schedules for peak hours",
                    "description": f"Your busiest hours are {peak_times}. Ensure maximum staff availability during these times.",
                    "reasoning": {
                        "peak_hours": peak_hours,
                        "avg_bookings_per_hour": hourly_patterns.get('hourly_averages', {}).get(peak_hours[0], {}).get('avg_bookings', 0),
                        "current_issue": "Potential wait times or rushed service"
                    },
                    "action_items": [
                        f"Schedule all experienced technicians for {peak_times}",
                        "Stagger break times to maintain coverage",
                        "Pre-prep stations before peak times",
                        "Consider adding express service options"
                    ],
                    "expected_impact": {
                        "customer_satisfaction": "+15%",
                        "wait_time_reduction": "25-35%",
                        "service_quality": "Improved consistency"
                    },
                    "confidence_score": 0.82
                })
            
        except Exception as e:
            self.logger.error(f"Error generating scheduling recommendations: {str(e)}")
        
        return recommendations
    
    async def generate_retention_recommendations(self) -> List[Dict[str, Any]]:
        """
        Generate customer retention recommendations based on:
        - Churn predictions
        - Customer lifetime value
        - Visit patterns
        """
        recommendations = []
        
        try:
            # Get churn analysis
            churn_analysis = await self.forecasting.identify_churn_risk(
                method="rule_based",
                threshold=0.7
            )
            
            if not churn_analysis.get('success'):
                return recommendations
            
            high_risk_customers = churn_analysis.get('high_risk_customers', [])
            
            # Recommendation 1: Win-back campaign for high-risk customers
            if len(high_risk_customers) >= 10:
                recommendations.append({
                    "type": "retention",
                    "priority": "critical",
                    "title": f"Launch win-back campaign for {len(high_risk_customers)} at-risk customers",
                    "description": f"You have {len(high_risk_customers)} high-value customers at risk of churning. "
                                 f"Launch targeted win-back campaign immediately.",
                    "reasoning": {
                        "at_risk_count": len(high_risk_customers),
                        "total_value_at_risk": sum(c['metrics']['total_spent'] for c in high_risk_customers[:20]),
                        "avg_risk_score": sum(c['churn_risk_score'] for c in high_risk_customers[:20]) / min(20, len(high_risk_customers)),
                        "urgency": "Critical - immediate action required"
                    },
                    "action_items": [
                        "Send personalized email with 20% discount offer",
                        "Make personal phone calls to top 5 customers",
                        "Create urgency with limited-time offer (7 days)",
                        "Highlight their favorite services/technicians",
                        "Ask for feedback on why they haven't visited"
                    ],
                    "expected_impact": {
                        "recovery_rate": "50-60% (10-12 customers)",
                        "revenue_recovered": f"${sum(c['metrics']['total_spent'] for c in high_risk_customers[:20]) * 0.55:.0f}",
                        "long_term_value": "Restored customer relationships"
                    },
                    "confidence_score": 0.85,
                    "data_sources": {
                        "customer_list": [c['customer_name'] for c in high_risk_customers[:10]],
                        "churn_model": "rule_based"
                    }
                })
            elif high_risk_customers:
                # Smaller list, more targeted approach
                recommendations.append({
                    "type": "retention",
                    "priority": "high",
                    "title": f"Personal outreach to {len(high_risk_customers)} at-risk customers",
                    "description": "A small number of valued customers haven't visited recently. "
                                 "Personal outreach is most effective for this group.",
                    "reasoning": {
                        "at_risk_count": len(high_risk_customers),
                        "approach": "Personal touch over mass campaign"
                    },
                    "action_items": [
                        "Make personal phone calls to each customer",
                        "Reference their service history in conversation",
                        "Offer personalized incentive (not generic discount)",
                        "Schedule appointment during call if possible"
                    ],
                    "expected_impact": {
                        "recovery_rate": "60-70%",
                        "customer_satisfaction": "Significantly improved",
                        "referral_potential": "High (impressed by personal attention)"
                    },
                    "confidence_score": 0.80
                })
            
            # Recommendation 2: VIP customer loyalty program
            clv_data = await self.forecasting.calculate_customer_lifetime_value()
            if clv_data.get('success'):
                vip_customers = [c for c in clv_data.get('customers', []) if c['customer_segment'] == 'VIP']
                
                if vip_customers:
                    recommendations.append({
                        "type": "retention",
                        "priority": "high",
                        "title": f"Launch VIP loyalty program for top {len(vip_customers)} customers",
                        "description": f"Your top {len(vip_customers)} customers represent "
                                     f"${clv_data.get('average_clv', 0) * len(vip_customers):.0f} in lifetime value. "
                                     f"Create exclusive VIP experience to maintain loyalty.",
                        "reasoning": {
                            "vip_count": len(vip_customers),
                            "avg_clv": f"${clv_data.get('average_clv', 0):.2f}",
                            "total_value": f"${clv_data.get('total_predicted_clv', 0):.0f}",
                            "retention_priority": "Critical to business"
                        },
                        "action_items": [
                            "Create VIP tier with exclusive perks",
                            "Offer priority booking and dedicated time slots",
                            "10% permanent discount or points program",
                            "Birthday/anniversary special treatments",
                            "Quarterly exclusive events or previews"
                        ],
                        "expected_impact": {
                            "vip_retention": "95%+ retention rate",
                            "referrals": "2-3 referrals per VIP per year",
                            "lifetime_value_increase": "15-20%",
                            "word_of_mouth": "Strong brand ambassadors"
                        },
                        "confidence_score": 0.90
                    })
            
            # Recommendation 3: Re-engagement for dormant customers
            query = """
            SELECT COUNT(*) as dormant_count
            FROM customers c
            LEFT JOIN bookings b ON c.id = b.customer_id
            WHERE b.booking_date < CURRENT_DATE - INTERVAL '90 days'
            OR b.id IS NULL
            """
            await self.db.execute(text(f"SET search_path TO {self.tenant_schema}"))
            result = await self.db.execute(text(query))
            row = result.fetchone()
            dormant_count = row[0] if row else 0
            
            if dormant_count > 20:
                recommendations.append({
                    "type": "retention",
                    "priority": "medium",
                    "title": f"Re-engage {dormant_count} dormant customers",
                    "description": f"{dormant_count} customers haven't visited in 90+ days. "
                                 f"Run re-engagement campaign to bring them back.",
                    "reasoning": {
                        "dormant_count": dormant_count,
                        "time_threshold": "90+ days",
                        "recovery_potential": "30-40% can be reactivated"
                    },
                    "action_items": [
                        "Create 'We Miss You' email campaign",
                        "Offer significant discount (25-30%) for first visit back",
                        "Survey to understand why they left",
                        "Highlight any new services or improvements",
                        "Make booking ultra-easy (one-click if possible)"
                    ],
                    "expected_impact": {
                        "reactivation_rate": "30-40%",
                        "recovered_customers": f"{int(dormant_count * 0.35)}",
                        "revenue_recovered": f"${dormant_count * 0.35 * 60:.0f}",
                        "feedback_value": "Learn why customers leave"
                    },
                    "confidence_score": 0.70
                })
            
        except Exception as e:
            self.logger.error(f"Error generating retention recommendations: {str(e)}")
        
        return recommendations
    
    async def generate_inventory_recommendations(self) -> List[Dict[str, Any]]:
        """
        Generate inventory recommendations based on:
        - Usage rates
        - Stock levels
        - Revenue forecasts
        """
        recommendations = []
        
        try:
            # Get product usage and stock data
            query = """
            WITH product_usage AS (
                SELECT 
                    p.id,
                    p.name as product_name,
                    p.current_stock,
                    p.min_stock_level,
                    COUNT(ps.id) as usage_count,
                    COUNT(ps.id)::float / 30 as avg_daily_usage,
                    CASE 
                        WHEN COUNT(ps.id)::float / 30 > 0 
                        THEN p.current_stock / (COUNT(ps.id)::float / 30)
                        ELSE 999
                    END as days_until_stockout
                FROM products p
                LEFT JOIN product_sales ps ON p.id = ps.product_id
                WHERE ps.sale_date >= CURRENT_DATE - INTERVAL '30 days'
                OR ps.id IS NULL
                GROUP BY p.id, p.name, p.current_stock, p.min_stock_level
            )
            SELECT *
            FROM product_usage
            WHERE current_stock < min_stock_level * 1.5
            OR days_until_stockout < 14
            ORDER BY days_until_stockout
            LIMIT 10
            """
            
            await self.db.execute(text(f"SET search_path TO {self.tenant_schema}"))
            result = await self.db.execute(text(query))
            low_stock_products = result.fetchall()
            
            # Recommendation 1: Immediate reorder for critical items
            critical_items = [p for p in low_stock_products if p.days_until_stockout < 7]
            if critical_items:
                product_list = ', '.join([p.product_name for p in critical_items[:5]])
                recommendations.append({
                    "type": "inventory",
                    "priority": "critical",
                    "title": f"URGENT: Reorder {len(critical_items)} products running out",
                    "description": f"Critical stock levels: {product_list}. "
                                 f"Will run out in < 7 days. Place orders immediately.",
                    "reasoning": {
                        "critical_count": len(critical_items),
                        "stockout_timeline": "< 7 days",
                        "business_impact": "Service disruption risk"
                    },
                    "action_items": [
                        f"Place rush order for: {product_list}",
                        "Contact supplier for expedited shipping",
                        "Check alternative suppliers as backup",
                        "Inform staff of limited availability",
                        "Consider service substitutions if needed"
                    ],
                    "expected_impact": {
                        "service_continuity": "Maintained",
                        "revenue_protection": "$1,000-2,000",
                        "customer_satisfaction": "Prevented disappointment"
                    },
                    "confidence_score": 0.95,
                    "data_sources": {
                        "products": [
                            {
                                "name": p.product_name,
                                "current_stock": p.current_stock,
                                "days_remaining": round(float(p.days_until_stockout), 1),
                                "daily_usage": round(float(p.avg_daily_usage), 1)
                            }
                            for p in critical_items[:5]
                        ]
                    }
                })
            
            # Recommendation 2: Standard reorder for low stock
            standard_reorder = [p for p in low_stock_products if 7 <= p.days_until_stockout < 14]
            if standard_reorder:
                recommendations.append({
                    "type": "inventory",
                    "priority": "high",
                    "title": f"Schedule reorder for {len(standard_reorder)} products",
                    "description": "Several products below optimal stock levels. "
                                 "Schedule reorder to maintain service continuity.",
                    "reasoning": {
                        "products_count": len(standard_reorder),
                        "stockout_timeline": "7-14 days",
                        "order_timing": "Standard lead time sufficient"
                    },
                    "action_items": [
                        "Review supplier stock availability",
                        "Place standard orders (3-5 day delivery)",
                        "Verify pricing and any bulk discounts",
                        "Update inventory management system",
                        "Set reorder alerts for future"
                    ],
                    "expected_impact": {
                        "inventory_optimization": "Maintained optimal levels",
                        "cost_efficiency": "Avoid rush shipping fees",
                        "service_quality": "Uninterrupted"
                    },
                    "confidence_score": 0.88
                })
            
            # Recommendation 3: Optimize inventory levels based on usage
            query_high_usage = """
            SELECT 
                p.name as product_name,
                COUNT(ps.id) as monthly_usage,
                p.current_stock,
                p.min_stock_level
            FROM products p
            JOIN product_sales ps ON p.id = ps.product_id
            WHERE ps.sale_date >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY p.id, p.name, p.current_stock, p.min_stock_level
            HAVING COUNT(ps.id) > p.min_stock_level * 2
            ORDER BY COUNT(ps.id) DESC
            LIMIT 5
            """
            
            result = await self.db.execute(text(query_high_usage))
            high_usage_products = result.fetchall()
            
            if high_usage_products:
                recommendations.append({
                    "type": "inventory",
                    "priority": "medium",
                    "title": "Increase min stock levels for popular products",
                    "description": "Some products sell much faster than your current min stock levels suggest. "
                                 "Adjust thresholds to prevent frequent stockouts.",
                    "reasoning": {
                        "analysis": "Usage exceeds min stock level by 2x+",
                        "recommendation": "Raise min stock levels",
                        "benefit": "Reduce reorder frequency and stockout risk"
                    },
                    "action_items": [
                        "Review usage patterns for top products",
                        "Increase min stock levels by 50-100%",
                        "Negotiate bulk pricing with supplier",
                        "Set up automated reorder triggers",
                        "Monitor for seasonal variations"
                    ],
                    "expected_impact": {
                        "stockout_reduction": "60-70%",
                        "ordering_efficiency": "Larger, less frequent orders",
                        "bulk_discount_savings": "10-15%",
                        "staff_time_saved": "2-3 hours/month"
                    },
                    "confidence_score": 0.75,
                    "data_sources": {
                        "high_usage_products": [
                            {
                                "name": p.product_name,
                                "monthly_usage": p.monthly_usage,
                                "current_min": p.min_stock_level,
                                "suggested_min": p.monthly_usage
                            }
                            for p in high_usage_products
                        ]
                    }
                })
            
        except Exception as e:
            self.logger.error(f"Error generating inventory recommendations: {str(e)}")
        
        return recommendations
    
    async def generate_pricing_recommendations(self) -> List[Dict[str, Any]]:
        """
        Generate pricing recommendations based on:
        - Demand elasticity
        - Competitive analysis
        - Service popularity
        """
        recommendations = []
        
        try:
            # Get service popularity and revenue data
            query = """
            WITH service_metrics AS (
                SELECT 
                    s.id,
                    s.name as service_name,
                    s.base_price,
                    s.category,
                    COUNT(bs.id) as booking_count,
                    AVG(b.total_amount) as avg_transaction,
                    COUNT(bs.id)::float / NULLIF(
                        (SELECT COUNT(*) FROM booking_services bs2 
                         JOIN bookings b2 ON bs2.booking_id = b2.id 
                         WHERE b2.booking_date >= CURRENT_DATE - INTERVAL '90 days'), 0
                    ) as market_share
                FROM services s
                LEFT JOIN booking_services bs ON s.id = bs.service_id
                LEFT JOIN bookings b ON bs.booking_id = b.id
                WHERE b.booking_date >= CURRENT_DATE - INTERVAL '90 days'
                GROUP BY s.id, s.name, s.base_price, s.category
            )
            SELECT *
            FROM service_metrics
            WHERE booking_count > 10
            ORDER BY booking_count DESC
            """
            
            await self.db.execute(text(f"SET search_path TO {self.tenant_schema}"))
            result = await self.db.execute(text(query))
            service_data = result.fetchall()
            
            # Recommendation 1: Price increase for high-demand services
            high_demand_services = [s for s in service_data if s.market_share > 0.15][:3]
            if high_demand_services:
                service = high_demand_services[0]
                new_price = float(service.base_price) * 1.10  # 10% increase
                recommendations.append({
                    "type": "pricing",
                    "priority": "medium",
                    "title": f"Consider pricing increase for {service.service_name}",
                    "description": f"{service.service_name} is highly popular ({service.booking_count} bookings in 90 days). "
                                 f"Demand suggests pricing power - test 10% increase.",
                    "reasoning": {
                        "current_price": f"${float(service.base_price):.2f}",
                        "suggested_price": f"${new_price:.2f}",
                        "market_share": f"{float(service.market_share) * 100:.1f}%",
                        "booking_count": service.booking_count,
                        "rationale": "High demand indicates customers value this service"
                    },
                    "action_items": [
                        f"Test new price ${new_price:.2f} (currently ${float(service.base_price):.2f})",
                        "Monitor booking volume for 30 days",
                        "Survey customers on perceived value",
                        "Compare with local competitor pricing",
                        "Roll back if bookings drop >20%"
                    ],
                    "expected_impact": {
                        "revenue_increase": f"${(new_price - float(service.base_price)) * service.booking_count:.0f}/quarter",
                        "demand_elasticity": "Low (high-demand service)",
                        "booking_impact": "Minimal expected drop (0-10%)",
                        "profit_margin": f"+{((new_price - float(service.base_price)) / float(service.base_price)) * 100:.1f}%"
                    },
                    "confidence_score": 0.72
                })
            
            # Recommendation 2: Bundle pricing for related services
            query_combinations = """
            WITH service_pairs AS (
                SELECT 
                    s1.name as service1,
                    s2.name as service2,
                    s1.base_price as price1,
                    s2.base_price as price2,
                    COUNT(*) as combo_count
                FROM booking_services bs1
                JOIN booking_services bs2 ON bs1.booking_id = bs2.booking_id AND bs1.id < bs2.id
                JOIN services s1 ON bs1.service_id = s1.id
                JOIN services s2 ON bs2.service_id = s2.id
                JOIN bookings b ON bs1.booking_id = b.id
                WHERE b.booking_date >= CURRENT_DATE - INTERVAL '90 days'
                GROUP BY s1.name, s2.name, s1.base_price, s2.base_price
                HAVING COUNT(*) > 5
                ORDER BY COUNT(*) DESC
                LIMIT 1
            )
            SELECT * FROM service_pairs
            """
            
            result = await self.db.execute(text(query_combinations))
            combo = result.fetchone()
            
            if combo:
                bundle_price = float(combo.price1 + combo.price2) * 0.85  # 15% bundle discount
                savings = float(combo.price1 + combo.price2) - bundle_price
                recommendations.append({
                    "type": "pricing",
                    "priority": "high",
                    "title": f"Create bundle: {combo.service1} + {combo.service2}",
                    "description": f"Customers frequently book {combo.service1} and {combo.service2} together "
                                 f"({combo.combo_count} times in 90 days). Create discounted bundle.",
                    "reasoning": {
                        "combination_frequency": combo.combo_count,
                        "individual_pricing": f"${float(combo.price1 + combo.price2):.2f}",
                        "bundle_pricing": f"${bundle_price:.2f}",
                        "customer_savings": f"${savings:.2f} (15%)",
                        "benefit": "Increase average ticket value"
                    },
                    "action_items": [
                        f"Create '{combo.service1} & {combo.service2} Package' at ${bundle_price:.2f}",
                        "Train staff to suggest bundle at booking",
                        "Feature bundle prominently on menu/website",
                        "Track bundle adoption rate",
                        "Consider seasonal variations"
                    ],
                    "expected_impact": {
                        "bundle_adoption": "30-40% of eligible customers",
                        "revenue_per_customer": f"+${bundle_price - float(combo.price1):.2f} per bundle",
                        "customer_satisfaction": "Higher (perceived value)",
                        "service_volume": f"+{int(combo.combo_count * 0.35)} bundles/quarter",
                        "quarterly_revenue_increase": f"${bundle_price * combo.combo_count * 0.35:.0f}"
                    },
                    "confidence_score": 0.85
                })
            
            # Recommendation 3: Dynamic pricing for off-peak times
            recommendations.append({
                "type": "pricing",
                "priority": "low",
                "title": "Implement dynamic pricing for slow periods",
                "description": "Consider variable pricing to optimize capacity utilization. "
                             "Offer discounts during slow times, premium during peak.",
                "reasoning": {
                    "strategy": "Dynamic pricing",
                    "benefit": "Maximize revenue per available hour",
                    "examples": "Airlines, hotels, ride-sharing"
                },
                "action_items": [
                    "Identify clear peak vs off-peak patterns",
                    "Offer 10-15% discount for off-peak bookings",
                    "Consider premium pricing (+10%) for prime Saturday slots",
                    "Implement booking system with time-based pricing",
                    "Communicate clearly to customers",
                    "Monitor acceptance and adjust"
                ],
                "expected_impact": {
                    "off_peak_utilization": "+20-30%",
                    "overall_revenue": "+8-12%",
                    "capacity_optimization": "Smoother demand distribution",
                    "implementation_timeline": "2-3 months"
                },
                "confidence_score": 0.65
            })
            
        except Exception as e:
            self.logger.error(f"Error generating pricing recommendations: {str(e)}")
        
        return recommendations
    
    async def save_recommendation(self, recommendation_data: Dict[str, Any]) -> Recommendation:
        """
        Save recommendation to database
        
        Args:
            recommendation_data: Recommendation details
            
        Returns:
            Recommendation object
        """
        try:
            recommendation = Recommendation(
                tenant_id=self.tenant_id,
                type=RecommendationType(recommendation_data['type']),
                priority=RecommendationPriority(recommendation_data['priority']),
                title=recommendation_data['title'],
                description=recommendation_data['description'],
                reasoning=recommendation_data.get('reasoning', {}),
                action_items=recommendation_data.get('action_items', []),
                expected_impact=recommendation_data.get('expected_impact', {}),
                confidence_score=recommendation_data.get('confidence_score'),
                data_sources=recommendation_data.get('data_sources', {}),
                expires_at=datetime.utcnow() + timedelta(days=30)  # 30-day expiration
            )
            
            self.db.add(recommendation)
            await self.db.commit()
            await self.db.refresh(recommendation)
            
            self.logger.info(f"Saved recommendation {recommendation.id} for tenant {self.tenant_id}")
            return recommendation
            
        except Exception as e:
            self.logger.error(f"Error saving recommendation: {str(e)}")
            await self.db.rollback()
            raise

