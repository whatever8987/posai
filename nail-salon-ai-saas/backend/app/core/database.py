"""
Multi-tenant database connection management
"""
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text, event
from contextlib import asynccontextmanager

from .config import settings

# Base class for models
Base = declarative_base()

# Engine for main database (stores tenant metadata)
engine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=False,
    future=True,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=40,
)

# Session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting database sessions
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


class TenantDatabase:
    """
    Manages tenant-specific database connections
    Uses PostgreSQL schema isolation for multi-tenancy
    """
    
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.schema_name = f"tenant_{tenant_id.replace('-', '_')}"
    
    async def get_session(self) -> AsyncSession:
        """Get a session with tenant schema set"""
        session = async_session_maker()
        
        # Set search_path to tenant schema
        await session.execute(
            text(f"SET search_path TO {self.schema_name}, public")
        )
        
        return session
    
    async def create_schema(self):
        """Create tenant schema and tables"""
        async with engine.begin() as conn:
            # Create schema
            await conn.execute(
                text(f"CREATE SCHEMA IF NOT EXISTS {self.schema_name}")
            )
            
            # Create tables in tenant schema
            await conn.execute(
                text(f"SET search_path TO {self.schema_name}")
            )
            
            # Create standard nail salon tables
            await self._create_tenant_tables(conn)
    
    async def _create_tenant_tables(self, conn):
        """Create the standard nail salon schema in tenant's schema"""
        # Customers table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS customers (
                customer_id SERIAL PRIMARY KEY,
                first_name VARCHAR(50) NOT NULL,
                last_name VARCHAR(50) NOT NULL,
                phone VARCHAR(20),
                email VARCHAR(100),
                date_of_birth DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT
            )
        """))
        
        # Technicians table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS technicians (
                technician_id SERIAL PRIMARY KEY,
                first_name VARCHAR(50) NOT NULL,
                last_name VARCHAR(50) NOT NULL,
                phone VARCHAR(20),
                email VARCHAR(100),
                specialties TEXT,
                hire_date DATE,
                is_active BOOLEAN DEFAULT TRUE,
                commission_rate DECIMAL(5,2) DEFAULT 50.00
            )
        """))
        
        # Services table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS services (
                service_id SERIAL PRIMARY KEY,
                service_name VARCHAR(100) NOT NULL,
                category VARCHAR(50) NOT NULL,
                base_price DECIMAL(10,2) NOT NULL,
                duration_minutes INT NOT NULL,
                description TEXT,
                is_active BOOLEAN DEFAULT TRUE
            )
        """))
        
        # Bookings table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS bookings (
                booking_id SERIAL PRIMARY KEY,
                customer_id INT NOT NULL,
                technician_id INT NOT NULL,
                booking_date DATE NOT NULL,
                booking_time TIME NOT NULL,
                status VARCHAR(20) DEFAULT 'scheduled',
                total_amount DECIMAL(10,2) NOT NULL,
                discount_amount DECIMAL(10,2) DEFAULT 0,
                tip_amount DECIMAL(10,2) DEFAULT 0,
                payment_method VARCHAR(50),
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
                FOREIGN KEY (technician_id) REFERENCES technicians(technician_id)
            )
        """))
        
        # Booking services junction table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS booking_services (
                booking_service_id SERIAL PRIMARY KEY,
                booking_id INT NOT NULL,
                service_id INT NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                FOREIGN KEY (booking_id) REFERENCES bookings(booking_id) ON DELETE CASCADE,
                FOREIGN KEY (service_id) REFERENCES services(service_id)
            )
        """))
        
        # Products table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS products (
                product_id SERIAL PRIMARY KEY,
                product_name VARCHAR(100) NOT NULL,
                category VARCHAR(50),
                unit_price DECIMAL(10,2) NOT NULL,
                current_stock INT DEFAULT 0,
                min_stock_level INT DEFAULT 10,
                supplier VARCHAR(100)
            )
        """))
        
        # Product sales table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS product_sales (
                sale_id SERIAL PRIMARY KEY,
                booking_id INT,
                product_id INT NOT NULL,
                quantity INT NOT NULL,
                unit_price DECIMAL(10,2) NOT NULL,
                total_price DECIMAL(10,2) NOT NULL,
                sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (booking_id) REFERENCES bookings(booking_id),
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            )
        """))
        
        print(f"Created tables in schema {self.schema_name}")
    
    async def drop_schema(self):
        """Delete tenant schema (for cleanup/testing)"""
        async with engine.begin() as conn:
            await conn.execute(
                text(f"DROP SCHEMA IF EXISTS {self.schema_name} CASCADE")
            )


async def init_db():
    """Initialize main database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

