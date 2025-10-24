"""
Base adapter class for POS integrations
All adapters must inherit from this class
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

from .standard_schema import STANDARD_SCHEMA, TableName


class AdapterType(str, Enum):
    """Types of adapters"""
    DATABASE = "database"      # Direct database connection
    API = "api"                # REST API integration
    FILE = "file"              # File-based import (CSV, JSON)
    WEBHOOK = "webhook"        # Webhook receiver


class SyncMode(str, Enum):
    """Data synchronization modes"""
    FULL = "full"              # Full data sync
    INCREMENTAL = "incremental"  # Only changed records
    REAL_TIME = "real_time"    # Real-time via webhooks


class BaseAdapter(ABC):
    """
    Abstract base class for all POS adapters
    
    Each adapter must implement these methods to integrate with a POS system
    """
    
    def __init__(self, tenant_id: str, credentials: Dict[str, Any], config: Dict[str, Any] = None):
        """
        Initialize adapter
        
        Args:
            tenant_id: Tenant identifier
            credentials: Connection credentials (API keys, DB connection strings, etc.)
            config: Additional configuration options
        """
        self.tenant_id = tenant_id
        self.credentials = credentials
        self.config = config or {}
        self.adapter_type = self._get_adapter_type()
        self.supported_tables = self._get_supported_tables()
    
    @abstractmethod
    def _get_adapter_type(self) -> AdapterType:
        """Return the type of this adapter"""
        pass
    
    @abstractmethod
    def _get_supported_tables(self) -> List[str]:
        """
        Return list of tables this adapter can sync
        
        Returns:
            List of table names from STANDARD_SCHEMA
        """
        pass
    
    @abstractmethod
    async def test_connection(self) -> tuple[bool, Optional[str]]:
        """
        Test the connection to the POS system
        
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        pass
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish connection to the POS system
        
        Returns:
            True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def disconnect(self):
        """Close connection to the POS system"""
        pass
    
    @abstractmethod
    async def sync_data(
        self,
        table_name: str,
        last_sync: Optional[datetime] = None,
        mode: SyncMode = SyncMode.INCREMENTAL
    ) -> Dict[str, Any]:
        """
        Sync data from POS system
        
        Args:
            table_name: Name of table to sync (from STANDARD_SCHEMA)
            last_sync: Timestamp of last successful sync
            mode: Sync mode (full or incremental)
        
        Returns:
            Dictionary with sync results:
            {
                "success": bool,
                "records_synced": int,
                "records_failed": int,
                "errors": List[str],
                "records": List[dict]  # The actual data
            }
        """
        pass
    
    @abstractmethod
    def get_schema_mapping(self) -> Dict[str, Dict[str, str]]:
        """
        Get mapping from POS schema to standard schema
        
        Returns:
            Dictionary mapping table names to field mappings:
            {
                "customers": {
                    "CustomerID": "customer_id",
                    "FirstName": "first_name",
                    ...
                },
                ...
            }
        """
        pass
    
    def map_record(self, table_name: str, source_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map a record from POS schema to standard schema
        
        Args:
            table_name: Table name
            source_record: Record in POS format
        
        Returns:
            Record in standard format
        """
        mapping = self.get_schema_mapping().get(table_name, {})
        mapped_record = {}
        
        for source_field, target_field in mapping.items():
            if source_field in source_record:
                value = source_record[source_field]
                # Apply any value transformations
                mapped_record[target_field] = self._transform_value(
                    target_field, value
                )
        
        return mapped_record
    
    def _transform_value(self, field_name: str, value: Any) -> Any:
        """
        Transform a value to match expected format
        
        Can be overridden by specific adapters for custom transformations
        """
        # Handle None values
        if value is None:
            return None
        
        # Convert dates
        if "date" in field_name and isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            except:
                return value
        
        # Convert booleans
        if field_name in ["is_active"] and isinstance(value, (str, int)):
            if isinstance(value, str):
                return value.lower() in ['true', '1', 'yes', 'active']
            return bool(value)
        
        # Convert decimals for money fields
        if any(x in field_name for x in ['price', 'amount', 'rate']) and value:
            try:
                return float(value)
            except:
                return value
        
        return value
    
    async def sync_all_tables(
        self,
        last_sync: Optional[datetime] = None,
        mode: SyncMode = SyncMode.INCREMENTAL
    ) -> Dict[str, Any]:
        """
        Sync all supported tables
        
        Args:
            last_sync: Timestamp of last successful sync
            mode: Sync mode
        
        Returns:
            Dictionary with overall sync results
        """
        results = {
            "success": True,
            "tables_synced": 0,
            "total_records": 0,
            "errors": [],
            "table_results": {}
        }
        
        for table_name in self.supported_tables:
            try:
                table_result = await self.sync_data(table_name, last_sync, mode)
                results["table_results"][table_name] = table_result
                
                if table_result["success"]:
                    results["tables_synced"] += 1
                    results["total_records"] += table_result["records_synced"]
                else:
                    results["success"] = False
                    results["errors"].extend(table_result.get("errors", []))
                    
            except Exception as e:
                results["success"] = False
                results["errors"].append(f"Error syncing {table_name}: {str(e)}")
        
        return results
    
    def validate_credentials(self) -> tuple[bool, Optional[str]]:
        """
        Validate that required credentials are present
        
        Returns:
            Tuple of (valid: bool, error_message: Optional[str])
        """
        required = self._get_required_credentials()
        missing = [key for key in required if key not in self.credentials]
        
        if missing:
            return False, f"Missing required credentials: {', '.join(missing)}"
        
        return True, None
    
    @abstractmethod
    def _get_required_credentials(self) -> List[str]:
        """
        Return list of required credential keys
        
        Example: ["api_key", "api_secret"] or ["host", "database", "username", "password"]
        """
        pass
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync status for this adapter"""
        return {
            "adapter_type": self.adapter_type,
            "supported_tables": self.supported_tables,
            "tenant_id": self.tenant_id,
        }

