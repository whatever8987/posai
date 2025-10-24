"""
Revenue Forecaster - Predict future revenue using time series analysis

Implements:
1. Simple Moving Average (Quick Win - Week 1)
2. Prophet Time Series Model (ML - Week 2)
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, date
import pandas as pd
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prediction import PredictionType, ModelType
from .base_predictor import BasePredictor


class RevenueForecaster(BasePredictor):
    """
    Revenue forecasting using multiple methods:
    - Moving Average (simple, fast)
    - Prophet (ML-based, seasonal)
    """
    
    def __init__(self, tenant_schema: str, db: AsyncSession):
        super().__init__(tenant_schema, db)
        self.default_ma_window = 30  # 30-day moving average
    
    def get_prediction_type(self) -> PredictionType:
        return PredictionType.REVENUE
    
    def get_model_type(self) -> ModelType:
        # Default to moving average for quick predictions
        return ModelType.MOVING_AVERAGE
    
    async def predict(
        self,
        days_ahead: int = 30,
        method: str = "moving_average",
        tenant_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate revenue forecast
        
        Args:
            days_ahead: Number of days to forecast
            method: "moving_average" or "prophet"
            tenant_id: Tenant ID for saving predictions
            
        Returns:
            Dict with forecast results
        """
        if method == "moving_average":
            return await self._forecast_moving_average(days_ahead, tenant_id)
        elif method == "prophet":
            return await self._forecast_prophet(days_ahead, tenant_id)
        else:
            raise ValueError(f"Unknown method: {method}")
    
    async def _forecast_moving_average(
        self,
        days_ahead: int,
        tenant_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Simple Moving Average Forecast - WEEK 1 QUICK WIN
        
        Fast, reliable baseline prediction using historical averages
        """
        try:
            # Fetch historical daily revenue
            query = f"""
            WITH daily_revenue AS (
                SELECT 
                    DATE(booking_date) as date,
                    SUM(total_amount) as revenue
                FROM bookings
                WHERE status = 'completed'
                AND booking_date >= CURRENT_DATE - INTERVAL '90 days'
                GROUP BY DATE(booking_date)
                ORDER BY date
            )
            SELECT 
                date,
                revenue,
                AVG(revenue) OVER (
                    ORDER BY date 
                    ROWS BETWEEN {self.default_ma_window} PRECEDING AND CURRENT ROW
                ) as ma_{self.default_ma_window}
            FROM daily_revenue
            ORDER BY date
            """
            
            df = await self.fetch_data(query)
            
            if df.empty:
                return {
                    "success": False,
                    "error": "No historical revenue data available",
                    "forecast": []
                }
            
            # Calculate moving average for forecast
            recent_ma = df[f'ma_{self.default_ma_window}'].iloc[-1]
            
            # Calculate day-of-week patterns
            df['day_of_week'] = pd.to_datetime(df['date']).dt.dayofweek
            dow_factors = df.groupby('day_of_week')['revenue'].mean() / df['revenue'].mean()
            
            # Generate forecast
            last_date = pd.to_datetime(df['date'].iloc[-1])
            forecast = []
            
            for i in range(1, days_ahead + 1):
                forecast_date = last_date + timedelta(days=i)
                dow = forecast_date.dayofweek
                dow_factor = dow_factors.get(dow, 1.0)
                
                # Simple forecast: MA * day-of-week factor
                predicted_revenue = recent_ma * dow_factor
                
                # Add confidence interval (±20% for simple model)
                lower = predicted_revenue * 0.8
                upper = predicted_revenue * 1.2
                
                forecast.append({
                    "date": forecast_date.strftime("%Y-%m-%d"),
                    "predicted_revenue": round(float(predicted_revenue), 2),
                    "lower_bound": round(float(lower), 2),
                    "upper_bound": round(float(upper), 2),
                    "confidence": 0.75  # 75% confidence for simple model
                })
            
            # Calculate summary statistics
            total_forecast = sum(f['predicted_revenue'] for f in forecast)
            avg_daily = total_forecast / days_ahead
            
            # Save predictions if tenant_id provided
            if tenant_id:
                for pred in forecast:
                    await self.save_prediction(
                        tenant_id=tenant_id,
                        predicted_value={"revenue": pred['predicted_revenue']},
                        confidence_interval={
                            "lower": pred['lower_bound'],
                            "upper": pred['upper_bound']
                        },
                        confidence_score=pred['confidence'],
                        target_date=datetime.strptime(pred['date'], "%Y-%m-%d").date(),
                        metadata={
                            "method": "moving_average",
                            "window": self.default_ma_window
                        },
                        valid_until=datetime.utcnow() + timedelta(days=7)  # Refresh weekly
                    )
            
            return {
                "success": True,
                "method": "moving_average",
                "forecast_days": days_ahead,
                "forecast": forecast,
                "summary": {
                    "total_forecast": round(total_forecast, 2),
                    "average_daily": round(avg_daily, 2),
                    "current_ma": round(float(recent_ma), 2)
                },
                "metadata": {
                    "training_data_points": len(df),
                    "ma_window": self.default_ma_window,
                    "confidence_level": "75%"
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in moving average forecast: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "forecast": []
            }
    
    async def _forecast_prophet(
        self,
        days_ahead: int,
        tenant_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Prophet Time Series Forecast - WEEK 2 ML MODEL
        
        Sophisticated ML model that handles:
        - Seasonality (day of week, monthly patterns)
        - Holidays
        - Trend changes
        """
        try:
            from prophet import Prophet
            
            # Fetch historical data (at least 2 months for Prophet)
            query = """
            WITH daily_revenue AS (
                SELECT 
                    DATE(booking_date) as date,
                    SUM(total_amount) as revenue
                FROM bookings
                WHERE status = 'completed'
                AND booking_date >= CURRENT_DATE - INTERVAL '180 days'
                GROUP BY DATE(booking_date)
                ORDER BY date
            )
            SELECT date, revenue
            FROM daily_revenue
            """
            
            df = await self.fetch_data(query)
            
            if len(df) < 60:  # Need at least 2 months
                return {
                    "success": False,
                    "error": "Insufficient historical data for Prophet (need 60+ days)",
                    "forecast": []
                }
            
            # Prepare data for Prophet (requires 'ds' and 'y' columns)
            prophet_df = pd.DataFrame({
                'ds': pd.to_datetime(df['date']),
                'y': df['revenue'].astype(float)
            })
            
            # Initialize and train Prophet model
            model = Prophet(
                yearly_seasonality=False,  # Not enough data
                weekly_seasonality=True,   # Day of week patterns
                daily_seasonality=False,
                changepoint_prior_scale=0.05,  # Flexibility in trend changes
                seasonality_prior_scale=10.0   # Strength of seasonality
            )
            
            # Fit model
            model.fit(prophet_df)
            
            # Generate future dates
            future = model.make_future_dataframe(periods=days_ahead, freq='D')
            forecast_df = model.predict(future)
            
            # Extract predictions for future days only
            future_predictions = forecast_df.tail(days_ahead)
            
            # Format results
            forecast = []
            for _, row in future_predictions.iterrows():
                forecast.append({
                    "date": row['ds'].strftime("%Y-%m-%d"),
                    "predicted_revenue": round(max(0, row['yhat']), 2),  # No negative revenue
                    "lower_bound": round(max(0, row['yhat_lower']), 2),
                    "upper_bound": round(max(0, row['yhat_upper']), 2),
                    "confidence": 0.85  # 85% confidence for Prophet
                })
            
            # Calculate metrics on historical data
            historical_predictions = forecast_df.iloc[:len(df)]
            y_true = prophet_df['y'].values
            y_pred = historical_predictions['yhat'].values
            metrics = self.calculate_metrics(y_true, y_pred)
            
            # Calculate summary
            total_forecast = sum(f['predicted_revenue'] for f in forecast)
            avg_daily = total_forecast / days_ahead
            
            # Save predictions if tenant_id provided
            if tenant_id:
                # Save model metadata
                await self.get_or_create_model(
                    tenant_id=tenant_id,
                    version=f"prophet_v1_{datetime.now().strftime('%Y%m%d')}",
                    performance_metrics=metrics,
                    training_config={
                        "training_samples": len(df),
                        "weekly_seasonality": True,
                        "changepoint_prior_scale": 0.05
                    }
                )
                
                # Save predictions
                for pred in forecast:
                    await self.save_prediction(
                        tenant_id=tenant_id,
                        predicted_value={"revenue": pred['predicted_revenue']},
                        confidence_interval={
                            "lower": pred['lower_bound'],
                            "upper": pred['upper_bound']
                        },
                        confidence_score=pred['confidence'],
                        target_date=datetime.strptime(pred['date'], "%Y-%m-%d").date(),
                        metadata={
                            "method": "prophet",
                            "metrics": metrics
                        },
                        valid_until=datetime.utcnow() + timedelta(days=7)
                    )
            
            return {
                "success": True,
                "method": "prophet",
                "forecast_days": days_ahead,
                "forecast": forecast,
                "summary": {
                    "total_forecast": round(total_forecast, 2),
                    "average_daily": round(avg_daily, 2)
                },
                "performance": metrics,
                "metadata": {
                    "training_data_points": len(df),
                    "model": "Prophet",
                    "confidence_level": "85%"
                }
            }
            
        except ImportError:
            return {
                "success": False,
                "error": "Prophet library not installed. Run: pip install prophet",
                "forecast": []
            }
        except Exception as e:
            self.logger.error(f"Error in Prophet forecast: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "forecast": []
            }
    
    async def get_revenue_anomalies(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Detect revenue anomalies in recent history
        Useful for automated insights
        """
        try:
            query = f"""
            WITH daily_stats AS (
                SELECT 
                    DATE(booking_date) as date,
                    SUM(total_amount) as revenue,
                    COUNT(*) as bookings
                FROM bookings
                WHERE status = 'completed'
                AND booking_date >= CURRENT_DATE - INTERVAL '{days_back} days'
                GROUP BY DATE(booking_date)
            ),
            stats AS (
                SELECT 
                    AVG(revenue) as mean_revenue,
                    STDDEV(revenue) as stddev_revenue
                FROM daily_stats
            )
            SELECT 
                ds.date,
                ds.revenue,
                ds.bookings,
                s.mean_revenue,
                s.stddev_revenue,
                (ds.revenue - s.mean_revenue) / NULLIF(s.stddev_revenue, 0) as z_score
            FROM daily_stats ds, stats s
            WHERE ABS((ds.revenue - s.mean_revenue) / NULLIF(s.stddev_revenue, 0)) > 2
            ORDER BY date DESC
            """
            
            df = await self.fetch_data(query)
            
            anomalies = []
            for _, row in df.iterrows():
                anomaly_type = "spike" if row['z_score'] > 2 else "drop"
                anomalies.append({
                    "date": str(row['date']),
                    "revenue": float(row['revenue']),
                    "expected": float(row['mean_revenue']),
                    "type": anomaly_type,
                    "severity": abs(float(row['z_score']))
                })
            
            return {
                "success": True,
                "anomalies": anomalies,
                "count": len(anomalies)
            }
            
        except Exception as e:
            self.logger.error(f"Error detecting anomalies: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "anomalies": []
            }

