"""
Prediction Models - Phase 4: Predictive Analytics

Stores ML model predictions and metadata
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, JSON, Date, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class PredictionType(str, enum.Enum):
    """Types of predictions"""
    REVENUE = "revenue"
    BOOKING_DEMAND = "booking_demand"
    CHURN_RISK = "churn_risk"
    SERVICE_TREND = "service_trend"
    CAPACITY = "capacity"
    CLV = "customer_lifetime_value"


class ModelType(str, enum.Enum):
    """Types of ML models"""
    PROPHET = "prophet"
    RANDOM_FOREST = "random_forest"
    LINEAR_REGRESSION = "linear_regression"
    GRADIENT_BOOSTING = "gradient_boosting"
    MOVING_AVERAGE = "moving_average"
    RULE_BASED = "rule_based"


class Prediction(Base):
    """Stores prediction results"""
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False)
    prediction_type = Column(Enum(PredictionType), nullable=False, index=True)
    model_type = Column(Enum(ModelType), nullable=False)
    
    # Prediction data
    target_date = Column(Date, nullable=True)  # For time-series predictions
    target_entity_id = Column(Integer, nullable=True)  # For customer-specific predictions
    predicted_value = Column(JSON, nullable=False)  # Flexible storage for different types
    
    # Confidence and metadata
    confidence_interval = Column(JSON, nullable=True)  # {"lower": x, "upper": y}
    confidence_score = Column(Float, nullable=True)  # 0-1 probability
    extra_data = Column(JSON, nullable=True)  # Additional context (renamed from metadata to avoid SQLAlchemy conflict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    valid_until = Column(DateTime, nullable=True)  # When prediction expires
    
    # Relationships
    tenant = relationship("Tenant", back_populates="predictions")
    
    def __repr__(self):
        return f"<Prediction {self.prediction_type} for tenant {self.tenant_id}>"


class MLModel(Base):
    """Stores ML model metadata and performance"""
    __tablename__ = "ml_models"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False)
    model_type = Column(Enum(ModelType), nullable=False)
    prediction_type = Column(Enum(PredictionType), nullable=False)
    
    # Model versioning
    version = Column(String(50), nullable=False)
    model_path = Column(String(500), nullable=True)  # Path to serialized model
    
    # Performance metrics
    performance_metrics = Column(JSON, nullable=True)  # {"mae": x, "rmse": y, "accuracy": z}
    feature_importance = Column(JSON, nullable=True)  # For tree-based models
    training_samples = Column(Integer, nullable=True)  # Number of samples used
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    trained_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    
    # Training configuration
    training_config = Column(JSON, nullable=True)  # Hyperparameters, features, etc.
    
    # Relationships
    tenant = relationship("Tenant", back_populates="ml_models")
    
    def __repr__(self):
        return f"<MLModel {self.model_type} v{self.version} for tenant {self.tenant_id}>"


class PredictionFeedback(Base):
    """Stores actual outcomes for model performance tracking"""
    __tablename__ = "prediction_feedback"

    id = Column(Integer, primary_key=True, index=True)
    prediction_id = Column(Integer, ForeignKey("predictions.id"), nullable=False)
    
    # Actual outcome
    actual_value = Column(JSON, nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Error metrics
    error = Column(Float, nullable=True)  # Calculated difference
    error_percentage = Column(Float, nullable=True)
    
    # Relationships
    prediction = relationship("Prediction")
    
    def __repr__(self):
        return f"<PredictionFeedback for prediction {self.prediction_id}>"

