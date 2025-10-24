"""
Customer Churn Predictor - Identify customers at risk of churning

Implements:
1. Rule-Based Churn Scoring (Quick Win - Week 1)
2. Random Forest Classifier (ML - Week 2)
3. Customer Lifetime Value (CLV) Calculation
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, date
import pandas as pd
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prediction import PredictionType, ModelType
from .base_predictor import BasePredictor


class ChurnPredictor(BasePredictor):
    """
    Predict customer churn risk using multiple methods
    """
    
    def __init__(self, tenant_schema: str, db: AsyncSession):
        super().__init__(tenant_schema, db)
    
    def get_prediction_type(self) -> PredictionType:
        return PredictionType.CHURN_RISK
    
    def get_model_type(self) -> ModelType:
        return ModelType.RULE_BASED  # Default to rule-based
    
    async def predict(
        self,
        method: str = "rule_based",
        threshold: float = 0.7,
        tenant_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Predict customer churn risk
        
        Args:
            method: "rule_based" or "random_forest"
            threshold: Risk threshold for classification (0-1)
            tenant_id: Tenant ID for saving predictions
            
        Returns:
            Dict with churn predictions
        """
        if method == "rule_based":
            return await self._predict_rule_based(threshold, tenant_id)
        elif method == "random_forest":
            return await self._predict_ml(threshold, tenant_id)
        else:
            raise ValueError(f"Unknown method: {method}")
    
    async def _predict_rule_based(
        self,
        threshold: float,
        tenant_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Rule-Based Churn Prediction - WEEK 1 QUICK WIN
        
        Uses business rules to score churn risk:
        - Days since last visit (recency)
        - Visit frequency decline
        - Spending trend
        - Customer value
        """
        try:
            # Fetch customer behavioral data
            query = """
            WITH customer_stats AS (
                SELECT 
                    c.id as customer_id,
                    c.first_name || ' ' || c.last_name as customer_name,
                    c.email,
                    c.phone,
                    COUNT(b.id) as total_visits,
                    SUM(b.total_amount) as total_spent,
                    MAX(b.booking_date) as last_visit_date,
                    MIN(b.booking_date) as first_visit_date,
                    AVG(b.total_amount) as avg_transaction,
                    CURRENT_DATE - MAX(b.booking_date) as days_since_last_visit
                FROM customers c
                LEFT JOIN bookings b ON c.id = b.customer_id AND b.status = 'completed'
                WHERE c.created_at < CURRENT_DATE - INTERVAL '30 days'  -- At least 30 days old
                GROUP BY c.id, c.first_name, c.last_name, c.email, c.phone
                HAVING COUNT(b.id) > 0  -- Has at least one visit
            ),
            recent_vs_old AS (
                SELECT 
                    cs.customer_id,
                    cs.customer_name,
                    cs.email,
                    cs.phone,
                    cs.total_visits,
                    cs.total_spent,
                    cs.last_visit_date,
                    cs.days_since_last_visit,
                    cs.avg_transaction,
                    -- Calculate visit frequency (visits per month)
                    CASE 
                        WHEN cs.first_visit_date = cs.last_visit_date THEN 0
                        ELSE cs.total_visits::float / 
                             GREATEST(1, EXTRACT(DAYS FROM (cs.last_visit_date - cs.first_visit_date)) / 30.0)
                    END as visit_frequency_per_month,
                    -- Recent activity (last 60 days)
                    (SELECT COUNT(*) 
                     FROM bookings b2 
                     WHERE b2.customer_id = cs.customer_id 
                     AND b2.booking_date >= CURRENT_DATE - INTERVAL '60 days'
                     AND b2.status = 'completed') as recent_visits
                FROM customer_stats cs
            )
            SELECT *
            FROM recent_vs_old
            """
            
            df = await self.fetch_data(query)
            
            if df.empty:
                return {
                    "success": False,
                    "error": "No customer data available",
                    "high_risk_customers": []
                }
            
            # Calculate churn risk score for each customer
            churn_predictions = []
            
            for _, customer in df.iterrows():
                risk_score = 0.0
                risk_factors = []
                
                # Factor 1: Days since last visit (weight: 0.4)
                days_since = customer['days_since_last_visit']
                if days_since > 90:
                    risk_score += 0.4
                    risk_factors.append(f"Last visit {days_since} days ago (>90 days)")
                elif days_since > 60:
                    risk_score += 0.25
                    risk_factors.append(f"Last visit {days_since} days ago (>60 days)")
                elif days_since > 45:
                    risk_score += 0.15
                    risk_factors.append(f"Last visit {days_since} days ago (>45 days)")
                
                # Factor 2: Visit frequency decline (weight: 0.3)
                if customer['recent_visits'] == 0 and customer['total_visits'] >= 3:
                    risk_score += 0.3
                    risk_factors.append("No visits in last 60 days despite being regular customer")
                elif customer['recent_visits'] < customer['visit_frequency_per_month'] / 2:
                    risk_score += 0.15
                    risk_factors.append("Visit frequency declined")
                
                # Factor 3: Customer value (weight: 0.3)
                # High-value customers leaving is more critical
                if customer['total_spent'] > 1000:
                    risk_score += 0.3 if risk_score > 0.3 else 0  # Amplify risk if already at risk
                    if risk_score >= 0.3:
                        risk_factors.append(f"High-value customer (${customer['total_spent']:.2f} lifetime value)")
                
                # Determine risk level
                if risk_score >= 0.7:
                    risk_level = "high"
                elif risk_score >= 0.4:
                    risk_level = "medium"
                else:
                    risk_level = "low"
                
                churn_predictions.append({
                    "customer_id": int(customer['customer_id']),
                    "customer_name": customer['customer_name'],
                    "email": customer['email'],
                    "phone": customer['phone'],
                    "churn_risk_score": round(risk_score, 2),
                    "risk_level": risk_level,
                    "risk_factors": risk_factors,
                    "metrics": {
                        "total_visits": int(customer['total_visits']),
                        "total_spent": float(customer['total_spent']),
                        "days_since_last_visit": int(days_since),
                        "avg_transaction": float(customer['avg_transaction']),
                        "visit_frequency_per_month": round(float(customer['visit_frequency_per_month']), 1)
                    }
                })
            
            # Filter high-risk customers
            high_risk = [c for c in churn_predictions if c['churn_risk_score'] >= threshold]
            high_risk.sort(key=lambda x: x['churn_risk_score'], reverse=True)
            
            # Save predictions if tenant_id provided
            if tenant_id:
                for pred in churn_predictions:
                    await self.save_prediction(
                        tenant_id=tenant_id,
                        predicted_value={
                            "churn_risk": pred['churn_risk_score'],
                            "risk_level": pred['risk_level']
                        },
                        confidence_score=pred['churn_risk_score'],
                        target_entity_id=pred['customer_id'],
                        metadata={
                            "method": "rule_based",
                            "risk_factors": pred['risk_factors'],
                            "metrics": pred['metrics']
                        },
                        valid_until=datetime.utcnow() + timedelta(days=7)
                    )
            
            return {
                "success": True,
                "method": "rule_based",
                "total_customers": len(churn_predictions),
                "high_risk_count": len(high_risk),
                "high_risk_customers": high_risk[:20],  # Top 20
                "summary": {
                    "high_risk": len([c for c in churn_predictions if c['risk_level'] == 'high']),
                    "medium_risk": len([c for c in churn_predictions if c['risk_level'] == 'medium']),
                    "low_risk": len([c for c in churn_predictions if c['risk_level'] == 'low'])
                },
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in rule-based churn prediction: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "high_risk_customers": []
            }
    
    async def _predict_ml(
        self,
        threshold: float,
        tenant_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        ML-Based Churn Prediction - WEEK 2 ML MODEL
        
        Uses Random Forest classifier with features:
        - Recency, Frequency, Monetary (RFM)
        - Visit trends
        - Service diversity
        - Seasonality patterns
        """
        try:
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.preprocessing import StandardScaler
            
            # Fetch comprehensive customer features
            query = """
            WITH customer_features AS (
                SELECT 
                    c.id as customer_id,
                    c.first_name || ' ' || c.last_name as customer_name,
                    c.email,
                    -- Recency
                    CURRENT_DATE - MAX(b.booking_date) as days_since_last_visit,
                    -- Frequency
                    COUNT(b.id) as total_visits,
                    COUNT(CASE WHEN b.booking_date >= CURRENT_DATE - INTERVAL '60 days' THEN 1 END) as recent_visits,
                    -- Monetary
                    SUM(b.total_amount) as total_spent,
                    AVG(b.total_amount) as avg_transaction,
                    -- Trends
                    STDDEV(b.total_amount) as spending_variability,
                    -- Service diversity
                    COUNT(DISTINCT bs.service_id) as unique_services_used,
                    -- Time-based
                    EXTRACT(DAYS FROM (MAX(b.booking_date) - MIN(b.booking_date))) as customer_tenure_days
                FROM customers c
                LEFT JOIN bookings b ON c.id = b.customer_id AND b.status = 'completed'
                LEFT JOIN booking_services bs ON b.id = bs.booking_id
                WHERE c.created_at < CURRENT_DATE - INTERVAL '60 days'
                GROUP BY c.id, c.first_name, c.last_name, c.email
                HAVING COUNT(b.id) >= 2  -- At least 2 visits for meaningful prediction
            )
            SELECT *,
                   -- Label as churned if no visit in 90+ days
                   CASE WHEN days_since_last_visit > 90 THEN 1 ELSE 0 END as churned
            FROM customer_features
            """
            
            df = await self.fetch_data(query)
            
            if len(df) < 30:  # Need minimum samples for ML
                return {
                    "success": False,
                    "error": "Insufficient customer data for ML model (need 30+ customers)",
                    "high_risk_customers": []
                }
            
            # Prepare features
            feature_columns = [
                'days_since_last_visit',
                'total_visits',
                'recent_visits',
                'total_spent',
                'avg_transaction',
                'spending_variability',
                'unique_services_used',
                'customer_tenure_days'
            ]
            
            # Handle missing values
            df[feature_columns] = df[feature_columns].fillna(0)
            
            X = df[feature_columns].values
            y = df['churned'].values
            
            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Train Random Forest
            model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                random_state=42,
                class_weight='balanced'  # Handle class imbalance
            )
            model.fit(X_scaled, y)
            
            # Predict churn probability
            churn_probabilities = model.predict_proba(X_scaled)[:, 1]
            
            # Get feature importance
            feature_importance = dict(zip(feature_columns, model.feature_importances_))
            
            # Build results
            churn_predictions = []
            for i, row in df.iterrows():
                churn_prob = float(churn_probabilities[i])
                
                # Determine risk level
                if churn_prob >= 0.7:
                    risk_level = "high"
                elif churn_prob >= 0.4:
                    risk_level = "medium"
                else:
                    risk_level = "low"
                
                churn_predictions.append({
                    "customer_id": int(row['customer_id']),
                    "customer_name": row['customer_name'],
                    "email": row['email'],
                    "churn_probability": round(churn_prob, 2),
                    "risk_level": risk_level,
                    "metrics": {
                        "days_since_last_visit": int(row['days_since_last_visit']),
                        "total_visits": int(row['total_visits']),
                        "total_spent": float(row['total_spent']),
                        "recent_visits": int(row['recent_visits'])
                    }
                })
            
            # Filter high-risk
            high_risk = [c for c in churn_predictions if c['churn_probability'] >= threshold]
            high_risk.sort(key=lambda x: x['churn_probability'], reverse=True)
            
            # Calculate model performance
            from sklearn.metrics import classification_report, roc_auc_score
            y_pred = (churn_probabilities >= 0.5).astype(int)
            
            # Save model and predictions if tenant_id provided
            if tenant_id:
                # Save model metadata
                await self.get_or_create_model(
                    tenant_id=tenant_id,
                    version=f"rf_v1_{datetime.now().strftime('%Y%m%d')}",
                    performance_metrics={
                        "roc_auc": float(roc_auc_score(y, churn_probabilities)),
                        "feature_importance": {k: float(v) for k, v in feature_importance.items()}
                    },
                    training_config={
                        "training_samples": len(df),
                        "features": feature_columns,
                        "model": "RandomForestClassifier"
                    }
                )
                
                # Save predictions
                for pred in churn_predictions:
                    await self.save_prediction(
                        tenant_id=tenant_id,
                        predicted_value={
                            "churn_probability": pred['churn_probability'],
                            "risk_level": pred['risk_level']
                        },
                        confidence_score=pred['churn_probability'],
                        target_entity_id=pred['customer_id'],
                        metadata={
                            "method": "random_forest",
                            "metrics": pred['metrics']
                        },
                        valid_until=datetime.utcnow() + timedelta(days=7)
                    )
            
            return {
                "success": True,
                "method": "random_forest",
                "total_customers": len(churn_predictions),
                "high_risk_count": len(high_risk),
                "high_risk_customers": high_risk[:20],
                "summary": {
                    "high_risk": len([c for c in churn_predictions if c['risk_level'] == 'high']),
                    "medium_risk": len([c for c in churn_predictions if c['risk_level'] == 'medium']),
                    "low_risk": len([c for c in churn_predictions if c['risk_level'] == 'low'])
                },
                "model_info": {
                    "roc_auc": float(roc_auc_score(y, churn_probabilities)),
                    "top_features": sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:5]
                },
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except ImportError:
            return {
                "success": False,
                "error": "scikit-learn not installed. Run: pip install scikit-learn",
                "high_risk_customers": []
            }
        except Exception as e:
            self.logger.error(f"Error in ML churn prediction: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "high_risk_customers": []
            }
    
    async def calculate_clv(self, customer_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Calculate Customer Lifetime Value (CLV)
        
        CLV = Average Transaction Value × Purchase Frequency × Customer Lifespan
        """
        try:
            # Build query
            where_clause = f"WHERE c.id = {customer_id}" if customer_id else ""
            
            query = f"""
            WITH customer_metrics AS (
                SELECT 
                    c.id as customer_id,
                    c.first_name || ' ' || c.last_name as customer_name,
                    COUNT(b.id) as total_visits,
                    SUM(b.total_amount) as total_spent,
                    AVG(b.total_amount) as avg_transaction_value,
                    MIN(b.booking_date) as first_visit,
                    MAX(b.booking_date) as last_visit,
                    EXTRACT(DAYS FROM (MAX(b.booking_date) - MIN(b.booking_date))) as customer_tenure_days,
                    -- Visit frequency (visits per month)
                    CASE 
                        WHEN EXTRACT(DAYS FROM (MAX(b.booking_date) - MIN(b.booking_date))) = 0 THEN 0
                        ELSE COUNT(b.id)::float / 
                             GREATEST(1, EXTRACT(DAYS FROM (MAX(b.booking_date) - MIN(b.booking_date))) / 30.0)
                    END as visits_per_month
                FROM customers c
                LEFT JOIN bookings b ON c.id = b.customer_id AND b.status = 'completed'
                {where_clause}
                GROUP BY c.id, c.first_name, c.last_name
                HAVING COUNT(b.id) > 0
            )
            SELECT 
                customer_id,
                customer_name,
                total_visits,
                total_spent,
                avg_transaction_value,
                visits_per_month,
                customer_tenure_days,
                -- Predicted CLV (assuming 3-year customer lifespan)
                avg_transaction_value * visits_per_month * 36 as predicted_clv_3year,
                -- Historical CLV
                total_spent as historical_clv
            FROM customer_metrics
            ORDER BY predicted_clv_3year DESC
            """
            
            df = await self.fetch_data(query)
            
            if df.empty:
                return {
                    "success": False,
                    "error": "No customer data available"
                }
            
            # Format results
            clv_results = []
            for _, row in df.iterrows():
                clv_results.append({
                    "customer_id": int(row['customer_id']),
                    "customer_name": row['customer_name'],
                    "historical_clv": round(float(row['historical_clv']), 2),
                    "predicted_clv_3year": round(float(row['predicted_clv_3year']), 2),
                    "avg_transaction_value": round(float(row['avg_transaction_value']), 2),
                    "visits_per_month": round(float(row['visits_per_month']), 2),
                    "customer_segment": self._segment_by_clv(float(row['predicted_clv_3year']))
                })
            
            return {
                "success": True,
                "customers": clv_results if customer_id else clv_results[:50],  # Top 50 if all customers
                "total_customers": len(clv_results),
                "average_clv": round(df['predicted_clv_3year'].mean(), 2),
                "total_predicted_clv": round(df['predicted_clv_3year'].sum(), 2)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating CLV: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _segment_by_clv(self, clv: float) -> str:
        """Segment customers by CLV"""
        if clv >= 2000:
            return "VIP"
        elif clv >= 1000:
            return "High Value"
        elif clv >= 500:
            return "Medium Value"
        else:
            return "Low Value"

