"""
CSV file importer adapter
Imports data from CSV files
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import csv
from pathlib import Path
import chardet

from ...base_adapter import BaseAdapter, AdapterType, SyncMode
from ...standard_schema import STANDARD_SCHEMA


class CSVAdapter(BaseAdapter):
    """
    Adapter for CSV file imports
    
    Credentials required:
    - file_path: Path to CSV file or directory containing CSV files
    
    Config options:
    - delimiter: CSV delimiter (default: ',')
    - encoding: File encoding (default: auto-detect)
    - has_header: Whether first row is header (default: True)
    """
    
    def __init__(self, tenant_id: str, credentials: Dict[str, Any], config: Dict[str, Any] = None):
        super().__init__(tenant_id, credentials, config)
        self.file_path = Path(credentials.get("file_path", ""))
        self.delimiter = config.get("delimiter", ",")
        self.has_header = config.get("has_header", True)
        self.encoding = config.get("encoding")
    
    def _get_adapter_type(self) -> AdapterType:
        return AdapterType.FILE
    
    def _get_supported_tables(self) -> List[str]:
        return list(STANDARD_SCHEMA.keys())
    
    def _get_required_credentials(self) -> List[str]:
        return ["file_path"]
    
    async def test_connection(self) -> tuple[bool, Optional[str]]:
        """Test if file/directory exists and is readable"""
        try:
            if not self.file_path.exists():
                return False, f"Path does not exist: {self.file_path}"
            
            if self.file_path.is_file():
                # Try to open and read first line
                with open(self.file_path, 'rb') as f:
                    f.readline()
                return True, None
            elif self.file_path.is_dir():
                # Check if directory has CSV files
                csv_files = list(self.file_path.glob("*.csv"))
                if not csv_files:
                    return False, "No CSV files found in directory"
                return True, None
            else:
                return False, "Path is neither file nor directory"
                
        except Exception as e:
            return False, f"Error accessing file: {str(e)}"
    
    async def connect(self) -> bool:
        """No connection needed for file imports"""
        return True
    
    async def disconnect(self):
        """No disconnection needed"""
        pass
    
    def _detect_encoding(self, file_path: Path) -> str:
        """Auto-detect file encoding"""
        if self.encoding:
            return self.encoding
        
        with open(file_path, 'rb') as f:
            raw_data = f.read(10000)  # Read first 10KB
            result = chardet.detect(raw_data)
            return result['encoding'] or 'utf-8'
    
    async def sync_data(
        self,
        table_name: str,
        last_sync: Optional[datetime] = None,
        mode: SyncMode = SyncMode.FULL  # File imports are always full sync
    ) -> Dict[str, Any]:
        """Import data from CSV file"""
        
        result = {
            "success": False,
            "records_synced": 0,
            "records_failed": 0,
            "errors": [],
            "records": []
        }
        
        try:
            # Determine which file to read
            csv_file = self._get_file_for_table(table_name)
            
            if not csv_file:
                result["errors"].append(f"No CSV file found for table: {table_name}")
                return result
            
            # Detect encoding
            encoding = self._detect_encoding(csv_file)
            
            # Read CSV
            with open(csv_file, 'r', encoding=encoding) as f:
                if self.has_header:
                    reader = csv.DictReader(f, delimiter=self.delimiter)
                else:
                    reader = csv.reader(f, delimiter=self.delimiter)
                
                for row_num, row in enumerate(reader, start=1):
                    try:
                        if isinstance(row, dict):
                            # Has headers
                            mapped_record = self.map_record(table_name, row)
                        else:
                            # No headers, use positional mapping
                            mapped_record = self._map_row_by_position(table_name, row)
                        
                        result["records"].append(mapped_record)
                        result["records_synced"] += 1
                        
                    except Exception as e:
                        result["records_failed"] += 1
                        result["errors"].append(f"Row {row_num}: {str(e)}")
            
            result["success"] = result["records_failed"] < result["records_synced"]
            
        except Exception as e:
            result["errors"].append(f"Import error: {str(e)}")
        
        return result
    
    def _get_file_for_table(self, table_name: str) -> Optional[Path]:
        """Get the CSV file for a given table"""
        if self.file_path.is_file():
            return self.file_path
        
        # Look for file named after table
        table_file = self.file_path / f"{table_name}.csv"
        if table_file.exists():
            return table_file
        
        # Check config for custom file mappings
        file_mappings = self.config.get("file_mappings", {})
        if table_name in file_mappings:
            custom_file = self.file_path / file_mappings[table_name]
            if custom_file.exists():
                return custom_file
        
        return None
    
    def _map_row_by_position(self, table_name: str, row: List[str]) -> Dict[str, Any]:
        """Map a row without headers using positional mapping"""
        schema_fields = STANDARD_SCHEMA.get(table_name, [])
        
        mapped_record = {}
        for i, field_name in enumerate(schema_fields):
            if i < len(row):
                mapped_record[field_name] = self._transform_value(field_name, row[i])
        
        return mapped_record
    
    def get_schema_mapping(self) -> Dict[str, Dict[str, str]]:
        """Get field mapping from CSV columns to standard schema"""
        # Default: assume CSV columns match standard schema
        default_mapping = {
            table_name: {field: field for field in fields}
            for table_name, fields in STANDARD_SCHEMA.items()
        }
        
        # Allow custom column mappings via config
        custom_mappings = self.config.get("column_mappings", {})
        
        # Merge custom mappings
        for table_name, field_mapping in custom_mappings.items():
            if table_name in default_mapping:
                default_mapping[table_name].update(field_mapping)
        
        return default_mapping
    
    async def validate_file(self, table_name: str) -> Dict[str, Any]:
        """Validate CSV file structure"""
        csv_file = self._get_file_for_table(table_name)
        
        if not csv_file:
            return {
                "valid": False,
                "error": f"No file found for table: {table_name}"
            }
        
        try:
            encoding = self._detect_encoding(csv_file)
            
            with open(csv_file, 'r', encoding=encoding) as f:
                reader = csv.DictReader(f, delimiter=self.delimiter)
                headers = reader.fieldnames
                
                # Check first few rows
                sample_rows = []
                for i, row in enumerate(reader):
                    sample_rows.append(row)
                    if i >= 5:  # Sample first 5 rows
                        break
                
                return {
                    "valid": True,
                    "headers": headers,
                    "sample_rows": sample_rows,
                    "row_count": sum(1 for _ in open(csv_file, encoding=encoding)) - 1
                }
                
        except Exception as e:
            return {
                "valid": False,
                "error": str(e)
            }

