"""
Vanna AI Service - Multi-tenant SQL generation
Wraps the existing Vanna implementation for SaaS use
"""
import os
from typing import Optional, List, Dict
from pathlib import Path
import redis
import json
import hashlib

# Disable ChromaDB telemetry to avoid errors
os.environ["ANONYMIZED_TELEMETRY"] = "False"

from vanna.ollama import Ollama
from vanna.chromadb import ChromaDB_VectorStore

from ..core.config import settings
from ..core.tenancy import get_current_tenant_id


class NailSalonVanna(ChromaDB_VectorStore, Ollama):
    """
    Custom Vanna class for Nail Salon POS
    Inherits from both ChromaDB for vector storage and Ollama for LLM
    """
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        Ollama.__init__(self, config=config)


class VannaService:
    """
    Multi-tenant Vanna service with caching and training management
    """
    
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.tenant_data_path = Path(settings.TENANT_DATA_PATH) / tenant_id
        self.tenant_data_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize Redis for caching (optional - falls back to no cache if unavailable)
        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=True,
                socket_connect_timeout=2,
            )
            # Test connection
            self.redis_client.ping()
            self.cache_enabled = True
        except Exception as e:
            print(f"Redis connection failed: {e}. Continuing without cache.")
            self.redis_client = None
            self.cache_enabled = False
        
        # Initialize Vanna
        self.vn = self._initialize_vanna()
    
    def _initialize_vanna(self) -> NailSalonVanna:
        """Initialize Vanna with tenant-specific configuration"""
        config = {
            'model': settings.OLLAMA_MODEL,
            'ollama_host': settings.OLLAMA_HOST,
            'num_ctx': settings.OLLAMA_NUM_CTX,
            'keep_alive': '30m',
            'path': str(self.tenant_data_path / 'chroma'),
            'options': {
                'temperature': 0.1  # Low for consistent SQL generation
            }
        }
        
        return NailSalonVanna(config=config)
    
    def _get_cache_key(self, question: str) -> str:
        """Generate cache key for a question"""
        question_hash = hashlib.md5(question.encode()).hexdigest()
        return f"query:{self.tenant_id}:{question_hash}"
    
    def _get_from_cache(self, question: str) -> Optional[str]:
        """Get cached SQL for a question"""
        if not self.cache_enabled or not self.redis_client:
            return None
        try:
            cache_key = self._get_cache_key(question)
            cached = self.redis_client.get(cache_key)
            return cached if cached else None
        except Exception:
            return None
    
    def _set_cache(self, question: str, sql: str, ttl: int = 3600):
        """Cache SQL for a question"""
        if not self.cache_enabled or not self.redis_client:
            return
        try:
            cache_key = self._get_cache_key(question)
            self.redis_client.setex(cache_key, ttl, sql)
        except Exception:
            pass  # Silently fail if cache is unavailable
    
    async def generate_sql(self, question: str, use_cache: bool = True) -> str:
        """
        Generate SQL from natural language question
        
        Args:
            question: Natural language question
            use_cache: Whether to use cached results
        
        Returns:
            Generated SQL query
        """
        # Check cache first
        if use_cache:
            cached_sql = self._get_from_cache(question)
            if cached_sql:
                return cached_sql
        
        # Generate SQL using Vanna
        sql = self.vn.generate_sql(question)
        
        # Cache the result
        if use_cache:
            self._set_cache(question, sql)
        
        return sql
    
    async def train_schema(self, ddl: str):
        """
        Train Vanna on database schema
        
        Args:
            ddl: DDL statement to train on
        """
        self.vn.train(ddl=ddl)
    
    async def train_documentation(self, documentation: str):
        """
        Train Vanna on business documentation
        
        Args:
            documentation: Documentation text
        """
        self.vn.train(documentation=documentation)
    
    async def train_question_sql(self, question: str, sql: str):
        """
        Train Vanna on question-SQL pairs
        
        Args:
            question: Natural language question
            sql: Corresponding SQL query
        """
        self.vn.train(question=question, sql=sql)
    
    def is_trained(self) -> bool:
        """
        Check if tenant has been trained
        
        Returns:
            True if training data exists
        """
        try:
            training_data = self.vn.get_training_data()
            return training_data and len(training_data) > 0
        except:
            return False
    
    async def auto_train_tenant_schema(self):
        """
        Automatically train on comprehensive standard nail salon schema
        Uses enhanced training data from Phase 2 integration work
        """
        # Check if already trained
        if self.is_trained():
            return {
                "already_trained": True,
                "message": "Tenant already has training data. Use retrain if you want to add more."
            }
        
        # Import training data (lazy import to avoid circular dependencies)
        import sys
        from pathlib import Path
        training_path = Path(__file__).parent.parent.parent / "training"
        sys.path.insert(0, str(training_path))
        
        try:
            from standard_schema_training import get_all_training_data
        except ImportError:
            # Fallback to basic training if enhanced training not available
            return await self._basic_training()
        
        training_data = get_all_training_data()
        
        results = {
            "tenant_id": self.tenant_id,
            "ddl_trained": False,
            "questions_trained": 0,
            "documentation_added": 0,
            "errors": []
        }
        
        try:
            # Train DDL (complete schema with all 7 tables)
            self.vn.train(ddl=training_data["ddl"])
            results["ddl_trained"] = True
            
            # Train question-SQL pairs (30+ examples)
            for example in training_data['questions']:
                try:
                    self.vn.train(
                        question=example['question'],
                        sql=example['sql']
                    )
                    results["questions_trained"] += 1
                except Exception as e:
                    results["errors"].append(f"Error training question: {str(e)}")
            
            # Add business documentation
            for doc in training_data['documentation']:
                try:
                    self.vn.train(
                        documentation=f"{doc['term']}: {doc['documentation']}"
                    )
                    results["documentation_added"] += 1
                except Exception as e:
                    results["errors"].append(f"Error adding documentation: {str(e)}")
            
            results["success"] = True
            return results
            
        except Exception as e:
            results["errors"].append(f"Fatal training error: {str(e)}")
            results["success"] = False
            return results
    
    async def _basic_training(self):
        """Fallback basic training if enhanced training not available"""
        # Train on PostgreSQL-specific documentation
        await self.train_documentation("""
            CRITICAL: This is a PostgreSQL database. Use PostgreSQL syntax:
            
            Date Functions:
            - CURRENT_DATE (not CURDATE())
            - CURRENT_TIMESTAMP (not NOW())
            - Date arithmetic: CURRENT_DATE - INTERVAL '7 days'
            - Extract parts: EXTRACT(MONTH FROM date)
            
            Status values: scheduled, completed, cancelled, no_show
            Only count 'completed' bookings for revenue calculations.
        """)
        
        # Train on basic schema
        schemas = [
            """CREATE TABLE customers (
                customer_id SERIAL PRIMARY KEY,
                first_name VARCHAR(50),
                last_name VARCHAR(50),
                phone VARCHAR(20),
                email VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE bookings (
                booking_id SERIAL PRIMARY KEY,
                customer_id INT,
                technician_id INT,
                booking_date DATE,
                booking_time TIME,
                status VARCHAR(20),
                total_amount DECIMAL(10,2),
                tip_amount DECIMAL(10,2)
            )""",
        ]
        
        for ddl in schemas:
            await self.train_schema(ddl)
        
        return {"success": True, "basic_training": True}
    
    async def get_training_data(self) -> List[Dict]:
        """Get all training data for this tenant"""
        # This would query ChromaDB for stored training data
        # Implementation depends on ChromaDB's API
        return []
    
    async def clear_cache(self):
        """Clear all cached queries for this tenant"""
        pattern = f"query:{self.tenant_id}:*"
        keys = self.redis_client.keys(pattern)
        if keys:
            self.redis_client.delete(*keys)


# Factory function to get VannaService for current tenant
def get_vanna_service(tenant_id: Optional[str] = None) -> VannaService:
    """
    Get VannaService instance for a tenant
    
    Args:
        tenant_id: Tenant ID, defaults to current tenant from context
    
    Returns:
        VannaService instance
    """
    if tenant_id is None:
        tenant_id = get_current_tenant_id()
        if not tenant_id:
            raise ValueError("No tenant context available")
    
    return VannaService(tenant_id)

