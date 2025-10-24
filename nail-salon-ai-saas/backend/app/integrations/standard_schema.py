"""
Standard schema definition for nail salon data
All POS adapters map their schemas to this standard format
"""
from typing import Dict, List
from enum import Enum


class TableName(str, Enum):
    """Standard table names"""
    CUSTOMERS = "customers"
    TECHNICIANS = "technicians"
    SERVICES = "services"
    BOOKINGS = "bookings"
    BOOKING_SERVICES = "booking_services"
    PRODUCTS = "products"
    PRODUCT_SALES = "product_sales"


# Standard schema definition
STANDARD_SCHEMA: Dict[str, List[str]] = {
    "customers": [
        "customer_id",          # Unique identifier
        "first_name",           # Required
        "last_name",            # Required
        "phone",                # Optional
        "email",                # Optional
        "date_of_birth",        # Optional
        "created_at",           # Timestamp
        "notes",                # Optional text
    ],
    "technicians": [
        "technician_id",        # Unique identifier
        "first_name",           # Required
        "last_name",            # Required
        "phone",                # Optional
        "email",                # Optional
        "specialties",          # Text, comma-separated
        "hire_date",            # Date
        "is_active",            # Boolean
        "commission_rate",      # Decimal (percentage)
    ],
    "services": [
        "service_id",           # Unique identifier
        "service_name",         # Required
        "category",             # Manicure, Pedicure, etc.
        "base_price",           # Decimal
        "duration_minutes",     # Integer
        "description",          # Optional text
        "is_active",            # Boolean
    ],
    "bookings": [
        "booking_id",           # Unique identifier
        "customer_id",          # Foreign key
        "technician_id",        # Foreign key
        "booking_date",         # Date
        "booking_time",         # Time
        "status",               # scheduled, completed, cancelled, no_show
        "total_amount",         # Decimal
        "discount_amount",      # Decimal, default 0
        "tip_amount",           # Decimal, default 0
        "payment_method",       # cash, credit_card, etc.
        "notes",                # Optional text
        "created_at",           # Timestamp
    ],
    "booking_services": [
        "booking_service_id",   # Unique identifier
        "booking_id",           # Foreign key
        "service_id",           # Foreign key
        "price",                # Decimal (actual price charged)
    ],
    "products": [
        "product_id",           # Unique identifier
        "product_name",         # Required
        "category",             # Optional
        "unit_price",           # Decimal
        "current_stock",        # Integer
        "min_stock_level",      # Integer
        "supplier",             # Optional
    ],
    "product_sales": [
        "sale_id",              # Unique identifier
        "booking_id",           # Foreign key (optional)
        "product_id",           # Foreign key
        "quantity",             # Integer
        "unit_price",           # Decimal
        "total_price",          # Decimal
        "sale_date",            # Timestamp
    ],
}


# Data types for each field
FIELD_TYPES = {
    # IDs
    "customer_id": "integer",
    "technician_id": "integer",
    "service_id": "integer",
    "booking_id": "integer",
    "booking_service_id": "integer",
    "product_id": "integer",
    "sale_id": "integer",
    
    # Names
    "first_name": "string",
    "last_name": "string",
    "full_name": "string",
    "service_name": "string",
    "product_name": "string",
    
    # Contact info
    "phone": "string",
    "email": "string",
    
    # Dates and times
    "date_of_birth": "date",
    "created_at": "datetime",
    "updated_at": "datetime",
    "booking_date": "date",
    "booking_time": "time",
    "hire_date": "date",
    "sale_date": "datetime",
    
    # Money
    "base_price": "decimal",
    "unit_price": "decimal",
    "total_amount": "decimal",
    "discount_amount": "decimal",
    "tip_amount": "decimal",
    "total_price": "decimal",
    "price": "decimal",
    "commission_rate": "decimal",
    
    # Numbers
    "duration_minutes": "integer",
    "quantity": "integer",
    "current_stock": "integer",
    "min_stock_level": "integer",
    
    # Booleans
    "is_active": "boolean",
    
    # Text
    "notes": "text",
    "description": "text",
    "specialties": "text",
    "category": "string",
    "status": "string",
    "payment_method": "string",
    "supplier": "string",
}


# Valid values for status fields
BOOKING_STATUSES = ["scheduled", "completed", "cancelled", "no_show"]
PAYMENT_METHODS = ["cash", "credit_card", "debit_card", "mobile_payment"]
SERVICE_CATEGORIES = [
    "Manicure",
    "Pedicure",
    "Gel/Shellac",
    "Acrylic/Extensions",
    "Nail Art",
    "Spa Services",
    "Polish Change",
]


def validate_record(table_name: str, record: dict) -> tuple[bool, List[str]]:
    """
    Validate a record against the standard schema
    
    Args:
        table_name: Name of the table
        record: Record data as dictionary
    
    Returns:
        Tuple of (is_valid, error_messages)
    """
    if table_name not in STANDARD_SCHEMA:
        return False, [f"Unknown table: {table_name}"]
    
    errors = []
    schema_fields = STANDARD_SCHEMA[table_name]
    
    # Check for required fields (non-optional)
    required_fields = ["first_name", "last_name", "service_name", "product_name", 
                      "booking_date", "total_amount"]
    
    for field in required_fields:
        if field in schema_fields and field not in record:
            errors.append(f"Missing required field: {field}")
    
    # Validate status values
    if "status" in record and record["status"] not in BOOKING_STATUSES:
        errors.append(f"Invalid status: {record['status']}")
    
    return len(errors) == 0, errors


def get_primary_key(table_name: str) -> str:
    """Get the primary key field name for a table"""
    pk_map = {
        "customers": "customer_id",
        "technicians": "technician_id",
        "services": "service_id",
        "bookings": "booking_id",
        "booking_services": "booking_service_id",
        "products": "product_id",
        "product_sales": "sale_id",
    }
    return pk_map.get(table_name, "id")


def get_foreign_keys(table_name: str) -> Dict[str, str]:
    """Get foreign key relationships for a table"""
    fk_map = {
        "bookings": {
            "customer_id": "customers",
            "technician_id": "technicians",
        },
        "booking_services": {
            "booking_id": "bookings",
            "service_id": "services",
        },
        "product_sales": {
            "booking_id": "bookings",
            "product_id": "products",
        },
    }
    return fk_map.get(table_name, {})

