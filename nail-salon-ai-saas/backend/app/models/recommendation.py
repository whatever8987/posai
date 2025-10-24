"""
Recommendation Models - Phase 5: Recommendation Engine

Stores AI-powered business recommendations for salon operations
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class RecommendationType(str, enum.Enum):
    """Types of recommendations"""
    PROMOTION = "promotion"
    SCHEDULING = "scheduling"
    RETENTION = "retention"
    INVENTORY = "inventory"
    PRICING = "pricing"
    SERVICE_BUNDLING = "service_bundling"


class RecommendationPriority(str, enum.Enum):
    """Priority levels for recommendations"""
    CRITICAL = "critical"  # Immediate action needed
    HIGH = "high"          # Action within 24-48 hours
    MEDIUM = "medium"      # Action within week
    LOW = "low"            # Optional optimization


class RecommendationStatus(str, enum.Enum):
    """Recommendation lifecycle status"""
    ACTIVE = "active"          # Available for action
    ACCEPTED = "accepted"      # User accepted recommendation
    REJECTED = "rejected"      # User rejected recommendation
    COMPLETED = "completed"    # Action completed
    EXPIRED = "expired"        # Time-sensitive recommendation expired


class Recommendation(Base):
    """AI-generated business recommendations"""
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False)
    
    # Recommendation metadata
    type = Column(Enum(RecommendationType), nullable=False, index=True)
    priority = Column(Enum(RecommendationPriority), nullable=False)
    status = Column(Enum(RecommendationStatus), default=RecommendationStatus.ACTIVE, nullable=False)
    
    # Content
    title = Column(String(500), nullable=False)
    description = Column(String(2000), nullable=False)
    reasoning = Column(JSON, nullable=False)  # Why this recommendation was made
    
    # Action details
    action_items = Column(JSON, nullable=False)  # Specific steps to take
    expected_impact = Column(JSON, nullable=True)  # Predicted benefits
    
    # Supporting data
    data_sources = Column(JSON, nullable=True)  # Predictions/insights used
    confidence_score = Column(Float, nullable=True)  # 0-1 confidence
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)  # Time-sensitive recommendations
    acted_on_at = Column(DateTime, nullable=True)
    
    # User feedback
    user_feedback = Column(JSON, nullable=True)  # User's response
    effectiveness_score = Column(Float, nullable=True)  # Actual impact (tracked later)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="recommendations")
    
    def __repr__(self):
        return f"<Recommendation {self.type} - {self.title}>"


class RecommendationTemplate(Base):
    """Templates for generating recommendations"""
    __tablename__ = "recommendation_templates"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(Enum(RecommendationType), nullable=False)
    name = Column(String(255), nullable=False)
    
    # Template content
    title_template = Column(String(500), nullable=False)
    description_template = Column(String(2000), nullable=False)
    
    # Generation rules
    trigger_conditions = Column(JSON, nullable=False)  # When to generate
    data_requirements = Column(JSON, nullable=False)   # What data needed
    
    # Configuration
    is_active = Column(Boolean, default=True, nullable=False)
    priority_default = Column(Enum(RecommendationPriority), nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<RecommendationTemplate {self.name}>"


class RecommendationMetrics(Base):
    """Track recommendation effectiveness"""
    __tablename__ = "recommendation_metrics"

    id = Column(Integer, primary_key=True, index=True)
    recommendation_id = Column(Integer, ForeignKey("recommendations.id"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False)
    
    # Predicted vs actual impact
    predicted_impact = Column(JSON, nullable=False)
    actual_impact = Column(JSON, nullable=True)
    
    # Tracking metrics
    acceptance_rate = Column(Float, nullable=True)  # % of users who accept this type
    completion_rate = Column(Float, nullable=True)   # % who complete action
    roi = Column(Float, nullable=True)               # Return on investment
    
    # Timing
    time_to_action = Column(Integer, nullable=True)  # Hours until user acted
    measured_at = Column(DateTime, nullable=True)    # When impact was measured
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    recommendation = relationship("Recommendation")
    
    def __repr__(self):
        return f"<RecommendationMetrics for recommendation {self.recommendation_id}>"

