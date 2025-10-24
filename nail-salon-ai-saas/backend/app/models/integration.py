"""
POS Integration configuration model
"""
from sqlalchemy import Column, String, DateTime, JSON, Boolean, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from ..core.database import Base


class Integration(Base):
    """
    Stores POS integration configurations for each tenant
    """
    __tablename__ = "integrations"
    
    integration_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False)
    
    # Integration type
    integration_type = Column(String(100), nullable=False)  # square, clover, database, csv, etc.
    integration_name = Column(String(255), nullable=False)  # User-friendly name
    
    # Credentials (encrypted in production)
    credentials = Column(JSON, nullable=False)  # Stores API keys, database connection strings, etc.
    
    # Configuration
    config = Column(JSON, default=dict)  # Additional configuration options
    schema_mapping = Column(JSON, default=dict)  # How POS schema maps to standard schema
    
    # Status
    is_active = Column(Boolean, default=True)
    status = Column(String(50), default="pending")  # pending, active, error, disabled
    last_error = Column(Text, nullable=True)
    
    # Sync metadata
    last_sync_at = Column(DateTime, nullable=True)
    next_sync_at = Column(DateTime, nullable=True)
    sync_frequency_minutes = Column(Integer, default=15)  # How often to sync
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self, include_credentials=False):
        data = {
            "integration_id": str(self.integration_id),
            "tenant_id": str(self.tenant_id),
            "integration_type": self.integration_type,
            "integration_name": self.integration_name,
            "is_active": self.is_active,
            "status": self.status,
            "last_sync_at": self.last_sync_at.isoformat() if self.last_sync_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        
        if include_credentials:
            data["credentials"] = self.credentials
            data["config"] = self.config
        
        return data

