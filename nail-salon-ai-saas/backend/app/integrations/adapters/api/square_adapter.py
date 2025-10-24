"""
Square POS API adapter
Integrates with Square API to sync salon data
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import httpx

from ...base_adapter import BaseAdapter, AdapterType, SyncMode
from ...standard_schema import STANDARD_SCHEMA


class SquareAdapter(BaseAdapter):
    """
    Adapter for Square POS API
    
    Credentials required:
    - access_token: Square API access token
    - location_id: Square location ID (optional, for multi-location)
    
    API Documentation: https://developer.squareup.com/reference/square
    """
    
    def __init__(self, tenant_id: str, credentials: Dict[str, Any], config: Dict[str, Any] = None):
        super().__init__(tenant_id, credentials, config)
        self.base_url = config.get("base_url", "https://connect.squareup.com/v2")
        self.client: Optional[httpx.AsyncClient] = None
        self.location_id = credentials.get("location_id")
    
    def _get_adapter_type(self) -> AdapterType:
        return AdapterType.API
    
    def _get_supported_tables(self) -> List[str]:
        # Square supports these tables
        return ["customers", "services", "bookings", "products"]
    
    def _get_required_credentials(self) -> List[str]:
        return ["access_token"]
    
    async def test_connection(self) -> tuple[bool, Optional[str]]:
        """Test Square API connection"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/locations",
                    headers=self._get_headers(),
                    timeout=10
                )
                
                if response.status_code == 200:
                    return True, None
                else:
                    return False, f"API returned status {response.status_code}"
                    
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
    
    async def connect(self) -> bool:
        """Initialize HTTP client"""
        try:
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=self._get_headers(),
                timeout=30.0
            )
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False
    
    async def disconnect(self):
        """Close HTTP client"""
        if self.client:
            await self.client.aclose()
            self.client = None
    
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for Square API"""
        return {
            "Authorization": f"Bearer {self.credentials['access_token']}",
            "Content-Type": "application/json",
            "Square-Version": "2023-12-13"  # API version
        }
    
    async def sync_data(
        self,
        table_name: str,
        last_sync: Optional[datetime] = None,
        mode: SyncMode = SyncMode.INCREMENTAL
    ) -> Dict[str, Any]:
        """Sync data from Square API"""
        
        if not self.client:
            await self.connect()
        
        result = {
            "success": False,
            "records_synced": 0,
            "records_failed": 0,
            "errors": [],
            "records": []
        }
        
        try:
            if table_name == "customers":
                records = await self._sync_customers(last_sync, mode)
            elif table_name == "services":
                records = await self._sync_services()
            elif table_name == "bookings":
                records = await self._sync_bookings(last_sync, mode)
            elif table_name == "products":
                records = await self._sync_products()
            else:
                result["errors"].append(f"Table {table_name} not supported")
                return result
            
            result["records"] = records
            result["records_synced"] = len(records)
            result["success"] = True
            
        except Exception as e:
            result["errors"].append(f"Sync error: {str(e)}")
        
        return result
    
    async def _sync_customers(
        self,
        last_sync: Optional[datetime],
        mode: SyncMode
    ) -> List[Dict[str, Any]]:
        """Sync customers from Square"""
        customers = []
        cursor = None
        
        while True:
            # Build search query
            query = {}
            if mode == SyncMode.INCREMENTAL and last_sync:
                query["filter"] = {
                    "updated_at": {
                        "start_at": last_sync.isoformat()
                    }
                }
            
            if cursor:
                query["cursor"] = cursor
            
            response = await self.client.post(
                "/customers/search",
                json=query
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Map Square customers to standard schema
            for customer in data.get("customers", []):
                customers.append(self._map_customer(customer))
            
            # Check for more pages
            cursor = data.get("cursor")
            if not cursor:
                break
        
        return customers
    
    def _map_customer(self, square_customer: Dict) -> Dict:
        """Map Square customer to standard schema"""
        return {
            "customer_id": square_customer.get("id"),
            "first_name": square_customer.get("given_name", ""),
            "last_name": square_customer.get("family_name", ""),
            "email": square_customer.get("email_address"),
            "phone": square_customer.get("phone_number"),
            "created_at": square_customer.get("created_at"),
            "notes": square_customer.get("note"),
        }
    
    async def _sync_services(self) -> List[Dict[str, Any]]:
        """Sync services (catalog items) from Square"""
        services = []
        cursor = None
        
        while True:
            params = {
                "types": "ITEM",  # Get service items
            }
            if cursor:
                params["cursor"] = cursor
            
            response = await self.client.get(
                "/catalog/list",
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Map Square items to services
            for item in data.get("objects", []):
                if item.get("type") == "ITEM":
                    services.append(self._map_service(item))
            
            cursor = data.get("cursor")
            if not cursor:
                break
        
        return services
    
    def _map_service(self, square_item: Dict) -> Dict:
        """Map Square catalog item to service"""
        item_data = square_item.get("item_data", {})
        variations = item_data.get("variations", [])
        
        # Get first variation for pricing
        base_price = 0
        if variations:
            price_money = variations[0].get("item_variation_data", {}).get("price_money", {})
            base_price = price_money.get("amount", 0) / 100  # Convert cents to dollars
        
        return {
            "service_id": square_item.get("id"),
            "service_name": item_data.get("name", ""),
            "category": item_data.get("category_id", ""),
            "base_price": base_price,
            "description": item_data.get("description"),
            "is_active": not item_data.get("is_deleted", False),
            "duration_minutes": 60,  # Default, Square doesn't track this
        }
    
    async def _sync_bookings(
        self,
        last_sync: Optional[datetime],
        mode: SyncMode
    ) -> List[Dict[str, Any]]:
        """Sync bookings (appointments) from Square"""
        bookings = []
        
        # Square uses Appointments API
        params = {
            "location_id": self.location_id,
        }
        
        if mode == SyncMode.INCREMENTAL and last_sync:
            params["start_at_min"] = last_sync.isoformat()
        
        response = await self.client.get(
            "/bookings",
            params=params
        )
        response.raise_for_status()
        
        data = response.json()
        
        for booking in data.get("bookings", []):
            bookings.append(self._map_booking(booking))
        
        return bookings
    
    def _map_booking(self, square_booking: Dict) -> Dict:
        """Map Square booking to standard schema"""
        # Parse start time
        start_at = square_booking.get("start_at")
        booking_date = None
        booking_time = None
        
        if start_at:
            dt = datetime.fromisoformat(start_at.replace('Z', '+00:00'))
            booking_date = dt.date()
            booking_time = dt.time()
        
        return {
            "booking_id": square_booking.get("id"),
            "customer_id": square_booking.get("customer_id"),
            "technician_id": square_booking.get("team_member_id"),
            "booking_date": booking_date,
            "booking_time": booking_time,
            "status": self._map_booking_status(square_booking.get("status")),
            "total_amount": 0,  # Need to fetch from payment
            "created_at": square_booking.get("created_at"),
        }
    
    def _map_booking_status(self, square_status: str) -> str:
        """Map Square booking status to standard status"""
        status_map = {
            "PENDING": "scheduled",
            "ACCEPTED": "scheduled",
            "COMPLETED": "completed",
            "CANCELLED": "cancelled",
            "NO_SHOW": "no_show",
        }
        return status_map.get(square_status, "scheduled")
    
    async def _sync_products(self) -> List[Dict[str, Any]]:
        """Sync retail products from Square catalog"""
        # Similar to services but filter for retail items
        return []
    
    def get_schema_mapping(self) -> Dict[str, Dict[str, str]]:
        """Square uses its own object structure, mapping handled in _map_* methods"""
        return {
            "customers": {},
            "services": {},
            "bookings": {},
            "products": {},
        }

