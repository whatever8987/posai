"""
Generate fake data for nail salon POS system
Creates realistic bookings, customers, and sales data

Installation:
    pip install faker

Usage:
    python generate_fake_data.py
"""

import psycopg2
from datetime import datetime, timedelta
import random

try:
    from faker import Faker
except ImportError:
    print("❌ Please install faker: pip install faker")
    exit(1)

# Initialize Faker
fake = Faker()

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'dbname': 'nail_salon_pos',
    'user': 'postgres1',
    'password': 'Hanoi.2389',
    'port': 5432
}

def connect_db():
    """Connect to PostgreSQL database"""
    return psycopg2.connect(**DB_CONFIG)

def generate_customers(conn, num=100):
    """Generate fake customers"""
    print(f"\n👥 Generating {num} customers...")
    
    cursor = conn.cursor()
    customers = []
    
    for i in range(num):
        first_name = fake.first_name()
        last_name = fake.last_name()
        phone = fake.phone_number()[:20]
        email = fake.email()
        date_of_birth = fake.date_of_birth(minimum_age=18, maximum_age=70)
        created_at = fake.date_time_between(start_date='-2y', end_date='now')
        
        cursor.execute("""
            INSERT INTO customers (first_name, last_name, phone, email, date_of_birth, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING customer_id
        """, (first_name, last_name, phone, email, date_of_birth, created_at))
        
        customer_id = cursor.fetchone()[0]
        customers.append(customer_id)
        
        if (i + 1) % 20 == 0:
            print(f"  ✓ Generated {i + 1}/{num} customers")
    
    conn.commit()
    print(f"  ✅ Created {num} customers")
    return customers

def get_existing_ids(conn):
    """Get existing IDs from database"""
    cursor = conn.cursor()
    
    cursor.execute("SELECT customer_id FROM customers")
    customer_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT technician_id FROM technicians")
    technician_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT service_id FROM services")
    service_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT product_id FROM products")
    product_ids = [row[0] for row in cursor.fetchall()]
    
    return customer_ids, technician_ids, service_ids, product_ids

def generate_bookings(conn, customer_ids, technician_ids, service_ids, num=500):
    """Generate fake bookings"""
    print(f"\n📅 Generating {num} bookings...")
    
    cursor = conn.cursor()
    booking_ids = []
    
    statuses = ['completed', 'completed', 'completed', 'scheduled', 'cancelled', 'no_show']
    status_weights = [50, 30, 10, 5, 3, 2]  # Weighted distribution
    
    payment_methods = ['credit_card', 'cash', 'debit_card', 'mobile_payment']
    
    # Generate bookings over the past 6 months
    start_date = datetime.now() - timedelta(days=180)
    end_date = datetime.now() + timedelta(days=30)  # Include future bookings
    
    for i in range(num):
        customer_id = random.choice(customer_ids)
        technician_id = random.choice(technician_ids)
        
        # Random date between start and end
        booking_date = fake.date_between(start_date=start_date, end_date=end_date)
        
        # Business hours: 9 AM to 7 PM
        hour = random.randint(9, 18)
        minute = random.choice([0, 15, 30, 45])
        booking_time = f"{hour:02d}:{minute:02d}:00"
        
        # Status (more completed for past dates, more scheduled for future)
        if booking_date > datetime.now().date():
            status = 'scheduled'
        else:
            status = random.choices(statuses, weights=status_weights)[0]
        
        # Amount between $25 and $150
        total_amount = round(random.uniform(25, 150), 2)
        
        # Discount (20% chance of discount)
        discount_amount = round(random.uniform(5, 15), 2) if random.random() < 0.2 else 0
        
        # Tips (for completed bookings)
        if status == 'completed':
            tip_percentage = random.choice([0.15, 0.18, 0.20, 0.25])
            tip_amount = round(total_amount * tip_percentage, 2)
            payment_method = random.choice(payment_methods)
        else:
            tip_amount = 0
            payment_method = None
        
        cursor.execute("""
            INSERT INTO bookings (
                customer_id, technician_id, booking_date, booking_time,
                status, total_amount, discount_amount, tip_amount, payment_method
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING booking_id
        """, (customer_id, technician_id, booking_date, booking_time,
              status, total_amount, discount_amount, tip_amount, payment_method))
        
        booking_id = cursor.fetchone()[0]
        booking_ids.append((booking_id, status))
        
        if (i + 1) % 100 == 0:
            print(f"  ✓ Generated {i + 1}/{num} bookings")
    
    conn.commit()
    print(f"  ✅ Created {num} bookings")
    return booking_ids

def generate_booking_services(conn, booking_ids, service_ids):
    """Generate services for each booking"""
    print(f"\n💅 Generating booking services...")
    
    cursor = conn.cursor()
    count = 0
    
    for booking_id, status in booking_ids:
        # Skip cancelled and no-show bookings
        if status in ['cancelled', 'no_show']:
            continue
        
        # Each booking gets 1-3 services
        num_services = random.choices([1, 2, 3], weights=[60, 30, 10])[0]
        selected_services = random.sample(service_ids, min(num_services, len(service_ids)))
        
        for service_id in selected_services:
            # Get service price (simplified - using random prices)
            price = round(random.uniform(15, 80), 2)
            
            cursor.execute("""
                INSERT INTO booking_services (booking_id, service_id, price)
                VALUES (%s, %s, %s)
            """, (booking_id, service_id, price))
            count += 1
    
    conn.commit()
    print(f"  ✅ Created {count} booking services")

def generate_product_sales(conn, booking_ids, product_ids):
    """Generate product sales"""
    print(f"\n🛍️  Generating product sales...")
    
    cursor = conn.cursor()
    count = 0
    
    for booking_id, status in booking_ids:
        # Only completed bookings have product sales
        if status != 'completed':
            continue
        
        # 30% chance of product sale
        if random.random() < 0.3:
            num_products = random.choices([1, 2], weights=[80, 20])[0]
            
            for _ in range(num_products):
                product_id = random.choice(product_ids)
                quantity = random.randint(1, 3)
                unit_price = round(random.uniform(5, 20), 2)
                total_price = round(unit_price * quantity, 2)
                
                cursor.execute("""
                    INSERT INTO product_sales (
                        booking_id, product_id, quantity, unit_price, total_price
                    ) VALUES (%s, %s, %s, %s, %s)
                """, (booking_id, product_id, quantity, unit_price, total_price))
                count += 1
    
    conn.commit()
    print(f"  ✅ Created {count} product sales")

def show_statistics(conn):
    """Show database statistics"""
    print("\n" + "=" * 60)
    print("📊 Database Statistics")
    print("=" * 60)
    
    cursor = conn.cursor()
    
    queries = [
        ("Total Customers", "SELECT COUNT(*) FROM customers"),
        ("Total Technicians", "SELECT COUNT(*) FROM technicians"),
        ("Total Services", "SELECT COUNT(*) FROM services"),
        ("Total Products", "SELECT COUNT(*) FROM products"),
        ("Total Bookings", "SELECT COUNT(*) FROM bookings"),
        ("  - Completed", "SELECT COUNT(*) FROM bookings WHERE status = 'completed'"),
        ("  - Scheduled", "SELECT COUNT(*) FROM bookings WHERE status = 'scheduled'"),
        ("  - Cancelled", "SELECT COUNT(*) FROM bookings WHERE status = 'cancelled'"),
        ("  - No Show", "SELECT COUNT(*) FROM bookings WHERE status = 'no_show'"),
        ("Total Revenue", "SELECT SUM(total_amount) FROM bookings WHERE status = 'completed'"),
        ("Total Tips", "SELECT SUM(tip_amount) FROM bookings WHERE status = 'completed'"),
        ("Product Sales", "SELECT COUNT(*) FROM product_sales"),
    ]
    
    for label, query in queries:
        cursor.execute(query)
        result = cursor.fetchone()[0]
        if isinstance(result, (int, float)) and result > 1000:
            print(f"{label:20} {result:>15,.2f}")
        else:
            print(f"{label:20} {result:>15}")

def main():
    print("=" * 60)
    print("  Fake Data Generator for Nail Salon POS")
    print("=" * 60)
    
    # Configuration
    NUM_CUSTOMERS = 100
    NUM_BOOKINGS = 500
    
    print(f"\n📋 Configuration:")
    print(f"  - Customers: {NUM_CUSTOMERS}")
    print(f"  - Bookings: {NUM_BOOKINGS}")
    print(f"  - Date Range: Last 6 months + next 30 days")
    
    try:
        # Connect to database
        print("\n🔌 Connecting to database...")
        conn = connect_db()
        print("  ✓ Connected to PostgreSQL")
        
        # Generate customers
        customer_ids = generate_customers(conn, NUM_CUSTOMERS)
        
        # Get existing IDs
        all_customer_ids, technician_ids, service_ids, product_ids = get_existing_ids(conn)
        
        # Generate bookings
        booking_ids = generate_bookings(conn, all_customer_ids, technician_ids, service_ids, NUM_BOOKINGS)
        
        # Generate booking services
        generate_booking_services(conn, booking_ids, service_ids)
        
        # Generate product sales
        generate_product_sales(conn, booking_ids, product_ids)
        
        # Show statistics
        show_statistics(conn)
        
        conn.close()
        
        print("\n" + "=" * 60)
        print("✅ Fake data generation complete!")
        print("=" * 60)
        print("\n💡 Try these queries now:")
        print("  - 'What is our total revenue for the last 3 months?'")
        print("  - 'Who are our top 20 customers by spending?'")
        print("  - 'Show daily revenue trend for last 30 days'")
        print("  - 'Which technician has the most bookings?'")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

