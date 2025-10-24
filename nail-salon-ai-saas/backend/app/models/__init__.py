"""
Database models
"""
from .tenant import Tenant
from .user import User
from .integration import Integration
from .query_history import QueryHistory
from .insight import Insight, InsightType, InsightSeverity, InsightStatus
from .prediction import Prediction, MLModel, PredictionFeedback, PredictionType, ModelType
from .recommendation import (
    Recommendation,
    RecommendationTemplate,
    RecommendationMetrics,
    RecommendationType,
    RecommendationPriority,
    RecommendationStatus
)

__all__ = [
    "Tenant",
    "User",
    "Integration",
    "QueryHistory",
    "Insight",
    "InsightType",
    "InsightSeverity",
    "InsightStatus",
    "Prediction",
    "MLModel",
    "PredictionFeedback",
    "PredictionType",
    "ModelType",
    "Recommendation",
    "RecommendationTemplate",
    "RecommendationMetrics",
    "RecommendationType",
    "RecommendationPriority",
    "RecommendationStatus"
]

