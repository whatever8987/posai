"""
MySQL database adapter
Connects directly to a MySQL database and syncs data
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import aiomysql

from ...base_adapter import BaseAdapter, AdapterType, SyncMode
from ...standard_schema import STANDARD_SCHEMA


class MySQLAdapter(BaseAdapter):
    """
    Adapter for MySQL/MariaDB databases
    
    Credentials required:
    - host: Database host
    - port: Database port (default: 3306)
    - database: Database name
    - username: Database user
    - password: Database password
    """
    
    def __init__(self, tenant_id: str, credentials: Dict[str, Any], config: Dict[str, Any] = None):
        super().__init__(tenant_id, credentials, config)
        self.connection: Optional[aiomysql.Connection] = None
        self.pool: Optional[aiomysql.Pool] = None
    
    def _get_adapter_type(self) -> AdapterType:
        return AdapterType.DATABASE
    
    def _get_supported_tables(self) -> List[str]:
        return list(STANDARD_SCHEMA.keys())
    
    def _get_required_credentials(self) -> List[str]:
        return ["host", "database", "username", "password"]
    
    async def test_connection(self) -> tuple[bool, Optional[str]]:
        """Test database connection"""
        try:
            conn = await aiomysql.connect(
                host=self.credentials["host"],
                port=self.credentials.get("port", 3306),
                db=self.credentials["database"],
                user=self.credentials["username"],
                password=self.credentials["password"],
                connect_timeout=10
            )
            conn.close()
            return True, None
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
    
    async def connect(self) -> bool:
        """Establish database connection pool"""
        try:
            self.pool = await aiomysql.create_pool(
                host=self.credentials["host"],
                port=self.credentials.get("port", 3306),
                db=self.credentials["database"],
                user=self.credentials["username"],
                password=self.credentials["password"],
                minsize=1,
                maxsize=10
            )
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False
    
    async def disconnect(self):
        """Close database connection pool"""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            self.pool = None
    
    async def sync_data(
        self,
        table_name: str,
        last_sync: Optional[datetime] = None,
        mode: SyncMode = SyncMode.INCREMENTAL
    ) -> Dict[str, Any]:
        """Sync data from MySQL table"""
        
        if not self.pool:
            await self.connect()
        
        result = {
            "success": False,
            "records_synced": 0,
            "records_failed": 0,
            "errors": [],
            "records": []
        }
        
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    # Get the actual table name from mapping
                    mapping = self.get_schema_mapping()
                    if table_name not in mapping:
                        result["errors"].append(f"No mapping found for table: {table_name}")
                        return result
                    
                    source_table = self.config.get("table_names", {}).get(table_name, table_name)
                    
                    # Build query
                    query = f"SELECT * FROM `{source_table}`"
                    params = []
                    
                    # Add incremental sync filter if applicable
                    if mode == SyncMode.INCREMENTAL and last_sync:
                        timestamp_col = self.config.get("timestamp_columns", {}).get(
                            table_name, "created_at"
                        )
                        query += f" WHERE `{timestamp_col}` > %s"
                        params.append(last_sync)
                    
                    await cursor.execute(query, params)
                    rows = await cursor.fetchall()
                    
                    # Map records to standard schema
                    for row in rows:
                        try:
                            mapped_record = self.map_record(table_name, row)
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
        """Get field mapping from source MySQL schema to standard schema"""
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
        if not self.pool:
            await self.connect()
        
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(f"DESCRIBE `{table_name}`")
                rows = await cursor.fetchall()
                
                return {
                    "columns": [
                        {
                            "name": row["Field"],
                            "type": row["Type"],
                            "nullable": row["Null"] == "YES",
                            "key": row["Key"],
                        }
                        for row in rows
                    ]
                }
    
    async def discover_tables(self) -> List[str]:
        """Discover available tables in the database"""
        if not self.pool:
            await self.connect()
        
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SHOW TABLES")
                rows = await cursor.fetchall()
                return [row[0] for row in rows]

