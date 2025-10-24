"""
Query history model for tracking natural language queries
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Float, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from ..core.database import Base


class QueryHistory(Base):
    """
    Tracks all natural language queries and their results
    Used for analytics, training, and usage tracking
    """
    __tablename__ = "query_history"
    
    query_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    
    # Query details
    question = Column(Text, nullable=False)  # Natural language question
    generated_sql = Column(Text, nullable=False)  # Generated SQL
    
    # Execution
    was_executed = Column(Boolean, default=False)
    execution_time_ms = Column(Float, nullable=True)
    row_count = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Feedback
    user_rating = Column(Integer, nullable=True)  # 1-5 stars
    user_feedback = Column(Text, nullable=True)
    was_helpful = Column(Boolean, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "query_id": str(self.query_id),
            "tenant_id": str(self.tenant_id),
            "user_id": str(self.user_id) if self.user_id else None,
            "question": self.question,
            "generated_sql": self.generated_sql,
            "was_executed": self.was_executed,
            "execution_time_ms": self.execution_time_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

