"""
PostgreSQL database adapter
Connects directly to a PostgreSQL database and syncs data
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncpg

from ...base_adapter import BaseAdapter, AdapterType, SyncMode
from ...standard_schema import STANDARD_SCHEMA


class PostgresAdapter(BaseAdapter):
    """
    Adapter for PostgreSQL databases
    
    Credentials required:
    - host: Database host
    - port: Database port (default: 5432)
    - database: Database name
    - username: Database user
    - password: Database password
    - schema: Schema name (optional, default: public)
    """
    
    def __init__(self, tenant_id: str, credentials: Dict[str, Any], config: Dict[str, Any] = None):
        super().__init__(tenant_id, credentials, config)
        self.connection: Optional[asyncpg.Connection] = None
        self.schema = credentials.get("schema", "public")
    
    def _get_adapter_type(self) -> AdapterType:
        return AdapterType.DATABASE
    
    def _get_supported_tables(self) -> List[str]:
        # All standard tables are supported
        return list(STANDARD_SCHEMA.keys())
    
    def _get_required_credentials(self) -> List[str]:
        return ["host", "database", "username", "password"]
    
    async def test_connection(self) -> tuple[bool, Optional[str]]:
        """Test database connection"""
        try:
            conn = await asyncpg.connect(
                host=self.credentials["host"],
                port=self.credentials.get("port", 5432),
                database=self.credentials["database"],
                user=self.credentials["username"],
                password=self.credentials["password"],
                timeout=10
            )
            await conn.close()
            return True, None
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
    
    async def connect(self) -> bool:
        """Establish database connection"""
        try:
            self.connection = await asyncpg.connect(
                host=self.credentials["host"],
                port=self.credentials.get("port", 5432),
                database=self.credentials["database"],
                user=self.credentials["username"],
                password=self.credentials["password"]
            )
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False
    
    async def disconnect(self):
        """Close database connection"""
        if self.connection:
            await self.connection.close()
            self.connection = None
    
    async def sync_data(
        self,
        table_name: str,
        last_sync: Optional[datetime] = None,
        mode: SyncMode = SyncMode.INCREMENTAL
    ) -> Dict[str, Any]:
        """Sync data from PostgreSQL table"""
        
        if not self.connection:
            await self.connect()
        
        result = {
            "success": False,
            "records_synced": 0,
            "records_failed": 0,
            "errors": [],
            "records": []
        }
        
        try:
            # Get the actual table name from mapping
            mapping = self.get_schema_mapping()
            if table_name not in mapping:
                result["errors"].append(f"No mapping found for table: {table_name}")
                return result
            
            source_table = self.config.get("table_names", {}).get(table_name, table_name)
            
            # Build query
            query = f"SELECT * FROM {self.schema}.{source_table}"
            
            # Add incremental sync filter if applicable
            if mode == SyncMode.INCREMENTAL and last_sync:
                # Assume tables have updated_at or created_at column
                timestamp_col = self.config.get("timestamp_columns", {}).get(
                    table_name, "created_at"
                )
                query += f" WHERE {timestamp_col} > $1"
                rows = await self.connection.fetch(query, last_sync)
            else:
                rows = await self.connection.fetch(query)
            
            # Map records to standard schema
            for row in rows:
                try:
                    # Convert asyncpg.Record to dict
                    source_record = dict(row)
                    mapped_record = self.map_record(table_name, source_record)
                    result["records"].append(mapped_record)
                    result["records_synced"] += 1
                except Exception as e:
                    result["records_failed"] += 1
                    result["errors"].append(f"Error mapping record: {str(e)}")
            
            result["success"] = result["records_failed"] == 0
            
        except Exception as e:
            result["errors"].append(f"Sync error: {str(e)}")
        
        return result
    
    def get_schema_mapping(self) -> Dict[str, Dict[str, str]]:
        """
        Get field mapping from source PostgreSQL schema to standard schema
        
        Can be customized via config
        """
        # Default mapping assumes source schema matches standard schema
        default_mapping = {
            table_name: {field: field for field in fields}
            for table_name, fields in STANDARD_SCHEMA.items()
        }
        
        # Allow custom mappings via config
        custom_mappings = self.config.get("schema_mappings", {})
        
        # Merge custom mappings
        for table_name, field_mapping in custom_mappings.items():
            if table_name in default_mapping:
                default_mapping[table_name].update(field_mapping)
        
        return default_mapping
    
    async def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Get information about a table in the source database"""
        if not self.connection:
            await self.connect()
        
        query = """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = $1 AND table_name = $2
            ORDER BY ordinal_position
        """
        
        rows = await self.connection.fetch(query, self.schema, table_name)
        
        return {
            "columns": [
                {
                    "name": row["column_name"],
                    "type": row["data_type"],
                    "nullable": row["is_nullable"] == "YES"
                }
                for row in rows
            ]
        }
    
    async def discover_tables(self) -> List[str]:
        """Discover available tables in the database"""
        if not self.connection:
            await self.connect()
        
        query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = $1 AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """
        
        rows = await self.connection.fetch(query, self.schema)
        return [row["table_name"] for row in rows]

