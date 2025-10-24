"""
Add PostgreSQL-specific training to your model
Run this to fix the syntax issues!

Usage:
    python train_postgres_syntax.py
"""

from vanna.ollama import Ollama
from vanna.chromadb import ChromaDB_VectorStore


class NailSalonVanna(ChromaDB_VectorStore, Ollama):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        Ollama.__init__(self, config=config)


def main():
    print("=" * 60)
    print("  Adding PostgreSQL-Specific Training")
    print("=" * 60)
    
    # Initialize with existing trained data
    vn = NailSalonVanna(config={
        'model': 'qwen2.5:7b',
        'num_ctx': 4096,
        'keep_alive': '30m',
        'path': './chroma_db_nail_salon'
    })
    
    print("\n📚 Training PostgreSQL syntax...")
    
    # PostgreSQL-specific documentation
    vn.train(documentation="""
        CRITICAL: This is a PostgreSQL database. Use PostgreSQL syntax:
        
        Date Functions:
        - CURRENT_DATE (not CURDATE())
        - CURRENT_TIMESTAMP (not NOW())
        - Date arithmetic: CURRENT_DATE - INTERVAL '7 days' (not DATE_SUB)
        - Date formatting: TO_CHAR(date, 'YYYY-MM-DD')
        - Extract parts: EXTRACT(MONTH FROM date)
        
        String Functions:
        - ILIKE (case-insensitive LIKE)
        - || for concatenation (not CONCAT)
        - POSITION('substr' IN string) or STRPOS
        
        Aggregates:
        - PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY col) for median
        - STRING_AGG for string concatenation
        
        Always use PostgreSQL syntax, never MySQL syntax!
    """)
    print("  ✓ PostgreSQL documentation added")
    
    # PostgreSQL-specific examples
    postgres_examples = [
        {
            "question": "What is our revenue for the last 7 days?",
            "sql": "SELECT SUM(total_amount) as weekly_revenue FROM bookings WHERE booking_date >= CURRENT_DATE - INTERVAL '7 days' AND status = 'completed'"
        },
        {
            "question": "What is our revenue this month?",
            "sql": "SELECT SUM(total_amount) as monthly_revenue FROM bookings WHERE EXTRACT(MONTH FROM booking_date) = EXTRACT(MONTH FROM CURRENT_DATE) AND EXTRACT(YEAR FROM booking_date) = EXTRACT(YEAR FROM CURRENT_DATE) AND status = 'completed'"
        },
        {
            "question": "Show customers who haven't visited in 60 days",
            "sql": "SELECT c.customer_id, c.first_name, c.last_name, c.phone, MAX(b.booking_date) as last_visit FROM customers c LEFT JOIN bookings b ON c.customer_id = b.customer_id GROUP BY c.customer_id, c.first_name, c.last_name, c.phone HAVING MAX(b.booking_date) < CURRENT_DATE - INTERVAL '60 days' OR MAX(b.booking_date) IS NULL ORDER BY last_visit"
        },
        {
            "question": "What are our top 10 customers by total spending?",
            "sql": "SELECT c.customer_id, c.first_name, c.last_name, SUM(b.total_amount) as total_spent FROM customers c JOIN bookings b ON c.customer_id = b.customer_id WHERE b.status = 'completed' GROUP BY c.customer_id, c.first_name, c.last_name ORDER BY total_spent DESC LIMIT 10"
        },
        {
            "question": "Which technician has the most appointments this week?",
            "sql": "SELECT t.technician_id, t.first_name, t.last_name, COUNT(b.booking_id) as appointment_count FROM technicians t JOIN bookings b ON t.technician_id = b.technician_id WHERE b.booking_date >= date_trunc('week', CURRENT_DATE) AND b.booking_date < date_trunc('week', CURRENT_DATE) + INTERVAL '1 week' GROUP BY t.technician_id, t.first_name, t.last_name ORDER BY appointment_count DESC LIMIT 1"
        },
        {
            "question": "Show appointments for today",
            "sql": "SELECT b.booking_id, b.booking_time, c.first_name || ' ' || c.last_name as customer_name, t.first_name || ' ' || t.last_name as technician_name, b.total_amount FROM bookings b JOIN customers c ON b.customer_id = c.customer_id JOIN technicians t ON b.technician_id = t.technician_id WHERE b.booking_date = CURRENT_DATE ORDER BY b.booking_time"
        },
        {
            "question": "What is the average revenue per day this month?",
            "sql": "SELECT AVG(daily_revenue) as avg_daily_revenue FROM (SELECT booking_date, SUM(total_amount) as daily_revenue FROM bookings WHERE EXTRACT(MONTH FROM booking_date) = EXTRACT(MONTH FROM CURRENT_DATE) AND EXTRACT(YEAR FROM booking_date) = EXTRACT(YEAR FROM CURRENT_DATE) AND status = 'completed' GROUP BY booking_date) as daily_totals"
        },
        {
            "question": "Show revenue by service category",
            "sql": "SELECT s.category, SUM(bs.price) as total_revenue FROM services s JOIN booking_services bs ON s.service_id = bs.service_id JOIN bookings b ON bs.booking_id = b.booking_id WHERE b.status = 'completed' GROUP BY s.category ORDER BY total_revenue DESC"
        },
        {
            "question": "How many new customers did we get this month?",
            "sql": "SELECT COUNT(*) as new_customers FROM customers WHERE EXTRACT(MONTH FROM created_at) = EXTRACT(MONTH FROM CURRENT_DATE) AND EXTRACT(YEAR FROM created_at) = EXTRACT(YEAR FROM CURRENT_DATE)"
        },
        {
            "question": "What are the most popular services?",
            "sql": "SELECT s.service_name, COUNT(bs.service_id) as booking_count FROM services s JOIN booking_services bs ON s.service_id = bs.service_id GROUP BY s.service_id, s.service_name ORDER BY booking_count DESC LIMIT 10"
        }
    ]
    
    for i, example in enumerate(postgres_examples, 1):
        vn.train(
            question=example['question'],
            sql=example['sql']
        )
        print(f"  ✓ Trained PostgreSQL example {i}/{len(postgres_examples)}")
    
    print("\n" + "=" * 60)
    print("✅ PostgreSQL training complete!")
    print("=" * 60)
    print("\n💡 Your model now knows PostgreSQL syntax!")
    print("   Try running: python use_vanna.py")


if __name__ == "__main__":
    main()

