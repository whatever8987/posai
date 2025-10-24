"""
Complete training script for Vanna AI with Nail Salon POS System
This script demonstrates how to set up and train Vanna for a nail salon database.

Usage:
    python train_nail_salon.py
"""

import json
import os
from typing import Optional

# Import Vanna components
try:
    from vanna.openai import OpenAI_Chat
    from vanna.chromadb import ChromaDB_VectorStore
except ImportError:
    print("Please install required packages:")
    print("pip install vanna chromadb openai")
    exit(1)


class NailSalonVanna(ChromaDB_VectorStore, OpenAI_Chat):
    """Custom Vanna class for Nail Salon POS"""
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(self, config=config)


def initialize_vanna(api_key: str, model: str = "gpt-4") -> NailSalonVanna:
    """
    Initialize Vanna with OpenAI and ChromaDB
    
    Args:
        api_key: OpenAI API key
        model: OpenAI model to use (default: gpt-4)
    
    Returns:
        Configured NailSalonVanna instance
    """
    config = {
        'api_key': api_key,
        'model': model,
        'path': './chroma_db_nail_salon'  # Local ChromaDB storage
    }
    
    vn = NailSalonVanna(config=config)
    print(f"✓ Vanna initialized with {model}")
    return vn


def train_database_schema(vn: NailSalonVanna) -> None:
    """Train Vanna with the nail salon database schema"""
    
    print("\n📊 Training database schema...")
    
    schemas = [
        {
            "name": "customers",
            "ddl": """
                CREATE TABLE customers (
                    customer_id INT PRIMARY KEY AUTO_INCREMENT,
                    first_name VARCHAR(50) NOT NULL,
                    last_name VARCHAR(50) NOT NULL,
                    phone VARCHAR(20),
                    email VARCHAR(100),
                    date_of_birth DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT,
                    INDEX idx_phone (phone),
                    INDEX idx_email (email)
                )
            """
        },
        {
            "name": "technicians",
            "ddl": """
                CREATE TABLE technicians (
                    technician_id INT PRIMARY KEY AUTO_INCREMENT,
                    first_name VARCHAR(50) NOT NULL,
                    last_name VARCHAR(50) NOT NULL,
                    phone VARCHAR(20),
                    specialties TEXT,
                    hire_date DATE,
                    is_active BOOLEAN DEFAULT TRUE,
                    commission_rate DECIMAL(5,2) DEFAULT 50.00
                )
            """
        },
        {
            "name": "services",
            "ddl": """
                CREATE TABLE services (
                    service_id INT PRIMARY KEY AUTO_INCREMENT,
                    service_name VARCHAR(100) NOT NULL,
                    category VARCHAR(50) NOT NULL,
                    base_price DECIMAL(10,2) NOT NULL,
                    duration_minutes INT NOT NULL,
                    description TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    INDEX idx_category (category)
                )
            """
        },
        {
            "name": "bookings",
            "ddl": """
                CREATE TABLE bookings (
                    booking_id INT PRIMARY KEY AUTO_INCREMENT,
                    customer_id INT NOT NULL,
                    technician_id INT NOT NULL,
                    booking_date DATE NOT NULL,
                    booking_time TIME NOT NULL,
                    status ENUM('scheduled', 'completed', 'cancelled', 'no_show') DEFAULT 'scheduled',
                    total_amount DECIMAL(10,2) NOT NULL,
                    discount_amount DECIMAL(10,2) DEFAULT 0,
                    tip_amount DECIMAL(10,2) DEFAULT 0,
                    payment_method VARCHAR(50),
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
                    FOREIGN KEY (technician_id) REFERENCES technicians(technician_id),
                    INDEX idx_booking_date (booking_date),
                    INDEX idx_status (status),
                    INDEX idx_customer (customer_id),
                    INDEX idx_technician (technician_id)
                )
            """
        },
        {
            "name": "booking_services",
            "ddl": """
                CREATE TABLE booking_services (
                    booking_service_id INT PRIMARY KEY AUTO_INCREMENT,
                    booking_id INT NOT NULL,
                    service_id INT NOT NULL,
                    price DECIMAL(10,2) NOT NULL,
                    FOREIGN KEY (booking_id) REFERENCES bookings(booking_id) ON DELETE CASCADE,
                    FOREIGN KEY (service_id) REFERENCES services(service_id),
                    INDEX idx_booking (booking_id),
                    INDEX idx_service (service_id)
                )
            """
        },
        {
            "name": "products",
            "ddl": """
                CREATE TABLE products (
                    product_id INT PRIMARY KEY AUTO_INCREMENT,
                    product_name VARCHAR(100) NOT NULL,
                    category VARCHAR(50),
                    unit_price DECIMAL(10,2) NOT NULL,
                    cost_price DECIMAL(10,2),
                    current_stock INT DEFAULT 0,
                    min_stock_level INT DEFAULT 10,
                    supplier VARCHAR(100),
                    sku VARCHAR(50) UNIQUE,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """
        },
        {
            "name": "product_sales",
            "ddl": """
                CREATE TABLE product_sales (
                    sale_id INT PRIMARY KEY AUTO_INCREMENT,
                    booking_id INT,
                    product_id INT NOT NULL,
                    quantity INT NOT NULL,
                    unit_price DECIMAL(10,2) NOT NULL,
                    total_price DECIMAL(10,2) NOT NULL,
                    sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (booking_id) REFERENCES bookings(booking_id),
                    FOREIGN KEY (product_id) REFERENCES products(product_id),
                    INDEX idx_sale_date (sale_date),
                    INDEX idx_product (product_id)
                )
            """
        }
    ]
    
    for schema in schemas:
        vn.train(ddl=schema["ddl"])
        print(f"  ✓ Trained table: {schema['name']}")


def train_business_documentation(vn: NailSalonVanna) -> None:
    """Train Vanna with business-specific terminology and rules"""
    
    print("\n📚 Training business documentation...")
    
    documentation = [
        {
            "name": "Service Categories",
            "content": """
                Service Categories in Nail Salon:
                - Manicure: Basic nail care and polish for hands (typically 30-45 minutes)
                - Pedicure: Basic nail care and polish for feet (typically 45-60 minutes)
                - Gel/Shellac: Long-lasting gel polish that requires UV curing (lasts 2-3 weeks)
                - Acrylic/Extensions: Artificial nail enhancements using acrylic or gel
                - Nail Art: Custom designs, decorations, and artistic work on nails
                - Spa Services: Premium treatments including massage and skin care
                - Polish Change: Quick service to change nail polish only
            """
        },
        {
            "name": "Booking Status",
            "content": """
                Booking Status Definitions:
                - scheduled: Appointment is confirmed and upcoming
                - completed: Customer showed up and service was provided successfully
                - cancelled: Customer cancelled the appointment before the scheduled time
                - no_show: Customer did not show up for their scheduled appointment
                
                Important: Only bookings with status='completed' should be counted for revenue calculations.
            """
        },
        {
            "name": "Revenue Metrics",
            "content": """
                Revenue and Payment Terms:
                - total_amount: The final amount charged to customer (includes services and products, after discounts)
                - discount_amount: Any promotions, coupons, or discounts applied
                - tip_amount: Gratuity given to technician (separate from total_amount, goes to technician)
                - payment_method: cash, credit_card, debit_card, mobile_payment
                
                Revenue Calculation:
                - Service Revenue = SUM(bookings.total_amount) WHERE status='completed'
                - Product Revenue = SUM(product_sales.total_price)
                - Total Revenue = Service Revenue + Product Revenue
                - Net Revenue = Total Revenue - discount_amount
            """
        },
        {
            "name": "Customer Segmentation",
            "content": """
                Customer Classifications:
                - New Customer: First booking within last 30 days
                - Regular Customer: 2 or more visits in last 90 days
                - VIP Customer: 10+ total visits OR $1000+ lifetime spend
                - Lapsed Customer: Last visit was more than 60 days ago
                - At-Risk Customer: Last visit was more than 90 days ago
                
                Customer Retention Rate = (Repeat Customers / Total Customers) * 100
                Where Repeat Customers are those with more than 1 completed booking.
            """
        },
        {
            "name": "Technician Performance",
            "content": """
                Technician Metrics:
                - Utilization Rate: (Actual appointment hours / Available hours) * 100
                - Average Ticket: Average total_amount per completed booking
                - Tips: Average and total tip_amount received
                - Rebooking Rate: Percentage of customers who book the same technician again
                - Commission: Usually percentage of service revenue (stored in commission_rate field)
            """
        },
        {
            "name": "Business Hours & Peak Times",
            "content": """
                Typical Business Hours: 9 AM to 7 PM, 7 days a week
                Peak Times:
                - Weekdays: Lunch hours (12-2 PM) and after work (5-7 PM)
                - Weekends: Mid-day (11 AM - 3 PM)
                - Peak Days: Friday, Saturday, Sunday
                - Slow Times: Monday morning, Tuesday morning
            """
        }
    ]
    
    for doc in documentation:
        vn.train(documentation=doc["content"])
        print(f"  ✓ Trained: {doc['name']}")


def train_sql_examples(vn: NailSalonVanna, json_file: Optional[str] = None) -> None:
    """Train Vanna with SQL question-answer pairs"""
    
    print("\n💡 Training SQL examples...")
    
    if json_file and os.path.exists(json_file):
        # Load from JSON file
        with open(json_file, 'r') as f:
            examples = json.load(f)
        
        for i, example in enumerate(examples, 1):
            vn.train(
                question=example['question'],
                sql=example['answer']
            )
            print(f"  ✓ Trained example {i}/{len(examples)}: {example['question'][:50]}...")
    else:
        # Use inline examples if file not found
        print("  ! JSON file not found, using inline examples")
        
        examples = [
            {
                "question": "What are the top 10 customers by total spending?",
                "sql": """
                    SELECT c.customer_id, c.first_name, c.last_name, 
                           SUM(b.total_amount) as total_spent
                    FROM customers c
                    JOIN bookings b ON c.customer_id = b.customer_id
                    WHERE b.status = 'completed'
                    GROUP BY c.customer_id, c.first_name, c.last_name
                    ORDER BY total_spent DESC
                    LIMIT 10
                """
            },
            {
                "question": "What is our total revenue for this month?",
                "sql": """
                    SELECT SUM(total_amount) as monthly_revenue
                    FROM bookings
                    WHERE MONTH(booking_date) = MONTH(CURRENT_DATE)
                      AND YEAR(booking_date) = YEAR(CURRENT_DATE)
                      AND status = 'completed'
                """
            }
        ]
        
        for i, example in enumerate(examples, 1):
            vn.train(question=example['question'], sql=example['sql'])
            print(f"  ✓ Trained example {i}/{len(examples)}")


def test_trained_model(vn: NailSalonVanna) -> None:
    """Test the trained model with sample questions"""
    
    print("\n🧪 Testing trained model...")
    
    test_questions = [
        "What are our top 5 customers by spending?",
        "How much revenue did we make today?",
        "Which technician has the most bookings this week?",
        "Show me customers who haven't visited in 60 days"
    ]
    
    for question in test_questions:
        print(f"\n  Question: {question}")
        try:
            sql = vn.generate_sql(question)
            print(f"  Generated SQL: {sql[:100]}...")
        except Exception as e:
            print(f"  Error: {str(e)}")


def connect_to_database(vn: NailSalonVanna, db_config: dict) -> None:
    """
    Connect Vanna to your actual database
    
    Args:
        vn: Vanna instance
        db_config: Database configuration dictionary
    """
    db_type = db_config.get('type', 'mysql')
    
    if db_type == 'mysql':
        vn.connect_to_mysql(
            host=db_config.get('host', 'localhost'),
            dbname=db_config.get('dbname', 'nail_salon_pos'),
            user=db_config.get('user'),
            password=db_config.get('password'),
            port=db_config.get('port', 3306)
        )
    elif db_type == 'postgres':
        vn.connect_to_postgres(
            host=db_config.get('host', 'localhost'),
            dbname=db_config.get('dbname', 'nail_salon_pos'),
            user=db_config.get('user'),
            password=db_config.get('password'),
            port=db_config.get('port', 5432)
        )
    elif db_type == 'sqlite':
        vn.connect_to_sqlite(db_config.get('path', 'nail_salon_pos.db'))
    
    print(f"✓ Connected to {db_type} database")


def main():
    """Main training workflow"""
    
    print("=" * 60)
    print("  Vanna AI Training: Nail Salon POS System")
    print("=" * 60)
    
    # Configuration
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    if not OPENAI_API_KEY:
        print("\n❌ Error: OPENAI_API_KEY environment variable not set")
        print("Set it with: export OPENAI_API_KEY='your-api-key'")
        return
    
    # Initialize Vanna
    vn = initialize_vanna(api_key=OPENAI_API_KEY, model='gpt-4')
    
    # Optional: Connect to actual database
    # Uncomment and configure if you have a database to connect to
    # db_config = {
    #     'type': 'mysql',
    #     'host': 'localhost',
    #     'dbname': 'nail_salon_pos',
    #     'user': 'root',
    #     'password': 'your_password',
    #     'port': 3306
    # }
    # connect_to_database(vn, db_config)
    
    # Training steps
    train_database_schema(vn)
    train_business_documentation(vn)
    
    # Try to load SQL examples from JSON file
    json_file = os.path.join(os.path.dirname(__file__), 'questions.json')
    train_sql_examples(vn, json_file)
    
    # Test the model
    test_trained_model(vn)
    
    print("\n" + "=" * 60)
    print("✅ Training complete!")
    print("=" * 60)
    print("\nYou can now use the trained model:")
    print("  sql = vn.generate_sql('Your question here')")
    print("  df = vn.run_sql(sql)")
    print("\nOr use the interactive interface:")
    print("  vn.ask('Your question here')")
    

if __name__ == "__main__":
    main()

