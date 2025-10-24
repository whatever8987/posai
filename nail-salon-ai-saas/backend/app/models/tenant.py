"""
Tenant (Salon) model
"""
from sqlalchemy import Column, String, DateTime, JSON, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from ..core.database import Base


class Tenant(Base):
    """
    Represents a salon account (tenant)
    Each tenant gets an isolated database schema
    """
    __tablename__ = "tenants"
    
    tenant_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    salon_name = Column(String(255), nullable=False)
    owner_email = Column(String(255), nullable=False, unique=True)
    
    # Subscription
    subscription_tier = Column(String(50), default="starter")  # starter, professional, enterprise
    subscription_status = Column(String(50), default="trial")  # trial, active, suspended, cancelled
    trial_ends_at = Column(DateTime, nullable=True)
    subscription_started_at = Column(DateTime, nullable=True)
    
    # Settings
    settings = Column(JSON, default=dict)  # Tenant-specific configurations
    
    # Integration status
    pos_integrated = Column(Boolean, default=False)
    pos_type = Column(String(100), nullable=True)  # square, clover, database, etc.
    last_sync_at = Column(DateTime, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Usage tracking
    query_count = Column(Integer, default=0)
    monthly_query_limit = Column(Integer, default=1000)
    
    # Relationships
    predictions = relationship("Prediction", back_populates="tenant", cascade="all, delete-orphan")
    ml_models = relationship("MLModel", back_populates="tenant", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="tenant", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            "tenant_id": str(self.tenant_id),
            "salon_name": self.salon_name,
            "owner_email": self.owner_email,
            "subscription_tier": self.subscription_tier,
            "subscription_status": self.subscription_status,
            "pos_integrated": self.pos_integrated,
            "pos_type": self.pos_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_active": self.is_active,
        }

