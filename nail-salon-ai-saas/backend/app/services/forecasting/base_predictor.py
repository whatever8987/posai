"""
Base Predictor Class - Abstract interface for all predictive models
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime, date
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import pandas as pd
import logging

from app.models.prediction import Prediction, MLModel, PredictionType, ModelType

logger = logging.getLogger(__name__)


class BasePredictor(ABC):
    """
    Abstract base class for all prediction models
    Provides common functionality for data fetching, model management, and prediction storage
    """
    
    def __init__(self, tenant_schema: str, db: AsyncSession):
        self.tenant_schema = tenant_schema
        self.db = db
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    async def predict(self, **kwargs) -> Dict[str, Any]:
        """
        Generate predictions
        Must be implemented by subclasses
        Returns: Dict with prediction results
        """
        pass
    
    @abstractmethod
    def get_prediction_type(self) -> PredictionType:
        """Return the type of prediction this model generates"""
        pass
    
    @abstractmethod
    def get_model_type(self) -> ModelType:
        """Return the type of model used"""
        pass
    
    async def fetch_data(self, query: str) -> pd.DataFrame:
        """
        Fetch data from tenant schema
        
        Args:
            query: SQL query string
            
        Returns:
            pandas DataFrame with results
        """
        try:
            # Set search path to tenant schema
            await self.db.execute(text(f"SET search_path TO {self.tenant_schema}"))
            
            # Execute query
            result = await self.db.execute(text(query))
            rows = result.fetchall()
            columns = result.keys()
            
            # Convert to DataFrame
            df = pd.DataFrame(rows, columns=columns)
            self.logger.info(f"Fetched {len(df)} rows from tenant schema {self.tenant_schema}")
            return df
            
        except Exception as e:
            self.logger.error(f"Error fetching data: {str(e)}")
            raise
    
    async def save_prediction(
        self,
        tenant_id: int,
        predicted_value: Dict[str, Any],
        confidence_interval: Optional[Dict[str, float]] = None,
        confidence_score: Optional[float] = None,
        target_date: Optional[date] = None,
        target_entity_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        valid_until: Optional[datetime] = None
    ) -> Prediction:
        """
        Save prediction to database
        
        Args:
            tenant_id: Tenant ID
            predicted_value: The prediction data
            confidence_interval: Optional confidence bounds
            confidence_score: Optional confidence score (0-1)
            target_date: Optional target date for time-series predictions
            target_entity_id: Optional entity ID for specific predictions
            metadata: Optional additional context
            valid_until: Optional expiration timestamp
            
        Returns:
            Prediction object
        """
        try:
            prediction = Prediction(
                tenant_id=tenant_id,
                prediction_type=self.get_prediction_type(),
                model_type=self.get_model_type(),
                predicted_value=predicted_value,
                confidence_interval=confidence_interval,
                confidence_score=confidence_score,
                target_date=target_date,
                target_entity_id=target_entity_id,
                metadata=metadata,
                valid_until=valid_until
            )
            
            self.db.add(prediction)
            await self.db.commit()
            await self.db.refresh(prediction)
            
            self.logger.info(f"Saved prediction {prediction.id} for tenant {tenant_id}")
            return prediction
            
        except Exception as e:
            self.logger.error(f"Error saving prediction: {str(e)}")
            await self.db.rollback()
            raise
    
    async def get_or_create_model(
        self,
        tenant_id: int,
        version: str,
        performance_metrics: Optional[Dict[str, Any]] = None,
        training_config: Optional[Dict[str, Any]] = None,
        model_path: Optional[str] = None
    ) -> MLModel:
        """
        Get existing model or create new one
        
        Args:
            tenant_id: Tenant ID
            version: Model version
            performance_metrics: Optional performance metrics
            training_config: Optional training configuration
            model_path: Optional path to serialized model
            
        Returns:
            MLModel object
        """
        try:
            # Check if model exists
            result = await self.db.execute(
                text("""
                    SELECT * FROM ml_models
                    WHERE tenant_id = :tenant_id
                    AND model_type = :model_type
                    AND prediction_type = :prediction_type
                    AND is_active = true
                    ORDER BY trained_at DESC
                    LIMIT 1
                """),
                {
                    "tenant_id": tenant_id,
                    "model_type": self.get_model_type().value,
                    "prediction_type": self.get_prediction_type().value
                }
            )
            existing_model = result.fetchone()
            
            if existing_model and existing_model.version == version:
                self.logger.info(f"Using existing model {existing_model.id}")
                return existing_model
            
            # Create new model
            model = MLModel(
                tenant_id=tenant_id,
                model_type=self.get_model_type(),
                prediction_type=self.get_prediction_type(),
                version=version,
                model_path=model_path,
                performance_metrics=performance_metrics,
                training_config=training_config
            )
            
            # Deactivate old models
            if existing_model:
                await self.db.execute(
                    text("""
                        UPDATE ml_models
                        SET is_active = false
                        WHERE tenant_id = :tenant_id
                        AND model_type = :model_type
                        AND prediction_type = :prediction_type
                    """),
                    {
                        "tenant_id": tenant_id,
                        "model_type": self.get_model_type().value,
                        "prediction_type": self.get_prediction_type().value
                    }
                )
            
            self.db.add(model)
            await self.db.commit()
            await self.db.refresh(model)
            
            self.logger.info(f"Created new model {model.id} version {version}")
            return model
            
        except Exception as e:
            self.logger.error(f"Error managing model: {str(e)}")
            await self.db.rollback()
            raise
    
    def calculate_metrics(self, y_true: List[float], y_pred: List[float]) -> Dict[str, float]:
        """
        Calculate common performance metrics
        
        Args:
            y_true: Actual values
            y_pred: Predicted values
            
        Returns:
            Dict with MAE, RMSE, MAPE
        """
        from sklearn.metrics import mean_absolute_error, mean_squared_error
        import numpy as np
        
        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        
        # Calculate MAPE (Mean Absolute Percentage Error)
        mape = np.mean(np.abs((np.array(y_true) - np.array(y_pred)) / np.array(y_true))) * 100
        
        # Calculate R² score
        from sklearn.metrics import r2_score
        r2 = r2_score(y_true, y_pred)
        
        return {
            "mae": float(mae),
            "rmse": float(rmse),
            "mape": float(mape),
            "r2_score": float(r2)
        }

