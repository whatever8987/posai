"""
Sync service for orchestrating data synchronization from POS systems
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import asyncio

from ..models import Integration, Tenant
from ..core.database import TenantDatabase
from ..core.tenancy import TenantContext
from ..integrations.base_adapter import BaseAdapter, SyncMode
from ..integrations.adapters.database.postgres_adapter import PostgresAdapter
from ..integrations.adapters.database.mysql_adapter import MySQLAdapter
from ..integrations.adapters.api.square_adapter import SquareAdapter
from ..integrations.adapters.file.csv_importer import CSVAdapter


class SyncService:
    """
    Service for managing data synchronization from POS systems
    """
    
    # Registry of available adapters
    ADAPTER_REGISTRY = {
        "postgres": PostgresAdapter,
        "mysql": MySQLAdapter,
        "square": SquareAdapter,
        "csv": CSVAdapter,
    }
    
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
    
    def get_adapter(
        self,
        integration_type: str,
        credentials: Dict[str, Any],
        config: Dict[str, Any] = None
    ) -> BaseAdapter:
        """
        Get an adapter instance for a given integration type
        
        Args:
            integration_type: Type of integration (postgres, mysql, square, etc.)
            credentials: Connection credentials
            config: Additional configuration
        
        Returns:
            Adapter instance
        
        Raises:
            ValueError: If integration type is not supported
        """
        adapter_class = self.ADAPTER_REGISTRY.get(integration_type)
        
        if not adapter_class:
            raise ValueError(f"Unsupported integration type: {integration_type}")
        
        return adapter_class(self.tenant_id, credentials, config)
    
    async def test_integration(
        self,
        integration_type: str,
        credentials: Dict[str, Any],
        config: Dict[str, Any] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Test an integration connection
        
        Args:
            integration_type: Type of integration
            credentials: Connection credentials
            config: Additional configuration
        
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        try:
            adapter = self.get_adapter(integration_type, credentials, config)
            
            # Validate credentials
            valid, error = adapter.validate_credentials()
            if not valid:
                return False, error
            
            # Test connection
            success, error = await adapter.test_connection()
            
            # Clean up
            await adapter.disconnect()
            
            return success, error
            
        except Exception as e:
            return False, f"Test failed: {str(e)}"
    
    async def sync_integration(
        self,
        integration_id: str,
        db: AsyncSession,
        mode: SyncMode = SyncMode.INCREMENTAL
    ) -> Dict[str, Any]:
        """
        Sync data from a configured integration
        
        Args:
            integration_id: Integration ID
            db: Database session
            mode: Sync mode (full or incremental)
        
        Returns:
            Sync results dictionary
        """
        # Get integration config
        from uuid import UUID
        result = await db.execute(
            select(Integration).where(Integration.integration_id == UUID(integration_id))
        )
        integration = result.scalar_one_or_none()
        
        if not integration:
            return {
                "success": False,
                "error": "Integration not found"
            }
        
        if integration.tenant_id != UUID(self.tenant_id):
            return {
                "success": False,
                "error": "Integration does not belong to this tenant"
            }
        
        try:
            # Create adapter
            adapter = self.get_adapter(
                integration.integration_type,
                integration.credentials,
                integration.config
            )
            
            # Connect
            await adapter.connect()
            
            # Sync all tables
            sync_results = await adapter.sync_all_tables(
                last_sync=integration.last_sync_at,
                mode=mode
            )
            
            # Write data to tenant's database
            if sync_results["success"]:
                await self._write_sync_data(
                    sync_results["table_results"],
                    db
                )
            
            # Update integration status
            integration.last_sync_at = datetime.utcnow()
            integration.status = "active" if sync_results["success"] else "error"
            
            if not sync_results["success"]:
                integration.last_error = "; ".join(sync_results["errors"])
            
            await db.commit()
            
            # Disconnect
            await adapter.disconnect()
            
            return sync_results
            
        except Exception as e:
            # Update integration with error
            integration.status = "error"
            integration.last_error = str(e)
            await db.commit()
            
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _write_sync_data(
        self,
        table_results: Dict[str, Dict[str, Any]],
        db: AsyncSession
    ):
        """
        Write synced data to tenant's database schema
        
        Args:
            table_results: Results from sync_all_tables
            db: Database session
        """
        tenant_db = TenantDatabase(self.tenant_id)
        session = await tenant_db.get_session()
        
        try:
            for table_name, result in table_results.items():
                if not result["success"]:
                    continue
                
                records = result.get("records", [])
                
                if not records:
                    continue
                
                # Upsert records (insert or update)
                await self._upsert_records(session, table_name, records)
            
            await session.commit()
            
        except Exception as e:
            await session.rollback()
            raise
        finally:
            await session.close()
    
    async def _upsert_records(
        self,
        session: AsyncSession,
        table_name: str,
        records: List[Dict[str, Any]]
    ):
        """
        Insert or update records in tenant's database
        
        Uses PostgreSQL's INSERT ... ON CONFLICT for upsert
        """
        from sqlalchemy import text
        from ..integrations.standard_schema import get_primary_key
        
        if not records:
            return
        
        pk_field = get_primary_key(table_name)
        
        # Build column list
        columns = list(records[0].keys())
        
        # Build INSERT statement
        columns_str = ", ".join(columns)
        placeholders = ", ".join([f":{col}" for col in columns])
        
        # Build UPDATE clause for ON CONFLICT
        update_clause = ", ".join([
            f"{col} = EXCLUDED.{col}" 
            for col in columns if col != pk_field
        ])
        
        query = f"""
            INSERT INTO {table_name} ({columns_str})
            VALUES ({placeholders})
            ON CONFLICT ({pk_field})
            DO UPDATE SET {update_clause}
        """
        
        # Execute for each record
        for record in records:
            await session.execute(text(query), record)
    
    async def schedule_sync(
        self,
        integration_id: str,
        db: AsyncSession
    ):
        """
        Schedule a sync job for an integration
        
        This would typically enqueue a Celery/RQ task
        For now, runs sync directly
        """
        return await self.sync_integration(integration_id, db)
    
    async def get_sync_status(
        self,
        integration_id: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Get sync status for an integration"""
        from uuid import UUID
        
        result = await db.execute(
            select(Integration).where(Integration.integration_id == UUID(integration_id))
        )
        integration = result.scalar_one_or_none()
        
        if not integration:
            return {"error": "Integration not found"}
        
        return {
            "integration_id": str(integration.integration_id),
            "integration_type": integration.integration_type,
            "status": integration.status,
            "last_sync_at": integration.last_sync_at.isoformat() if integration.last_sync_at else None,
            "next_sync_at": integration.next_sync_at.isoformat() if integration.next_sync_at else None,
            "last_error": integration.last_error,
        }
    
    @classmethod
    def get_supported_integrations(cls) -> List[str]:
        """Get list of supported integration types"""
        return list(cls.ADAPTER_REGISTRY.keys())

