# Training Vanna for Nail Salon POS System

This guide shows you how to train Vanna to generate SQL queries for your nail salon POS database.

## Prerequisites

```bash
pip install vanna
pip install chromadb  # or your preferred vector database
```

## Database Schema

Your nail salon POS should have tables like:
- **customers**: Customer information
- **technicians**: Staff members performing services
- **services**: Available services (manicure, pedicure, etc.)
- **bookings**: Appointment bookings
- **booking_services**: Services included in each booking (many-to-many)
- **products**: Retail products
- **product_sales**: Product sales transactions
- **payments**: Payment records

## Training Steps

### Step 1: Initialize Vanna

```python
from vanna.openai import OpenAI_Chat
from vanna.chromadb import ChromaDB_VectorStore

# Create your custom Vanna class
class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(self, config=config)

# Initialize with your API key
vn = MyVanna(config={
    'api_key': 'your-openai-api-key',
    'model': 'gpt-4',
    'path': './chroma_db_nail_salon'  # Local storage for ChromaDB
})

# Connect to your database
vn.connect_to_mysql(
    host='localhost',
    dbname='nail_salon_pos',
    user='your_username',
    password='your_password',
    port=3306
)
```

### Step 2: Train with DDL (Database Schema)

```python
# Train with your table structures
vn.train(ddl="""
    CREATE TABLE customers (
        customer_id INT PRIMARY KEY AUTO_INCREMENT,
        first_name VARCHAR(50),
        last_name VARCHAR(50),
        phone VARCHAR(20),
        email VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        notes TEXT
    )
""")

vn.train(ddl="""
    CREATE TABLE technicians (
        technician_id INT PRIMARY KEY AUTO_INCREMENT,
        first_name VARCHAR(50),
        last_name VARCHAR(50),
        phone VARCHAR(20),
        specialties TEXT,
        hire_date DATE,
        is_active BOOLEAN DEFAULT TRUE
    )
""")

vn.train(ddl="""
    CREATE TABLE services (
        service_id INT PRIMARY KEY AUTO_INCREMENT,
        service_name VARCHAR(100),
        category VARCHAR(50), -- manicure, pedicure, nail_art, etc.
        base_price DECIMAL(10,2),
        duration_minutes INT,
        description TEXT
    )
""")

vn.train(ddl="""
    CREATE TABLE bookings (
        booking_id INT PRIMARY KEY AUTO_INCREMENT,
        customer_id INT,
        technician_id INT,
        booking_date DATE,
        booking_time TIME,
        status ENUM('scheduled', 'completed', 'cancelled', 'no_show'),
        total_amount DECIMAL(10,2),
        discount_amount DECIMAL(10,2) DEFAULT 0,
        tip_amount DECIMAL(10,2) DEFAULT 0,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
        FOREIGN KEY (technician_id) REFERENCES technicians(technician_id)
    )
""")

vn.train(ddl="""
    CREATE TABLE booking_services (
        booking_service_id INT PRIMARY KEY AUTO_INCREMENT,
        booking_id INT,
        service_id INT,
        price DECIMAL(10,2),
        FOREIGN KEY (booking_id) REFERENCES bookings(booking_id),
        FOREIGN KEY (service_id) REFERENCES services(service_id)
    )
""")

vn.train(ddl="""
    CREATE TABLE products (
        product_id INT PRIMARY KEY AUTO_INCREMENT,
        product_name VARCHAR(100),
        category VARCHAR(50),
        unit_price DECIMAL(10,2),
        current_stock INT,
        min_stock_level INT,
        supplier VARCHAR(100)
    )
""")

vn.train(ddl="""
    CREATE TABLE product_sales (
        sale_id INT PRIMARY KEY AUTO_INCREMENT,
        booking_id INT,
        product_id INT,
        quantity INT,
        unit_price DECIMAL(10,2),
        total_price DECIMAL(10,2),
        sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (booking_id) REFERENCES bookings(booking_id),
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    )
""")
```

### Step 3: Train with Business Documentation

```python
# Add business-specific terminology and rules
vn.train(documentation="""
    Service Categories:
    - Manicure: Basic nail care for hands
    - Pedicure: Basic nail care for feet
    - Gel/Shellac: Long-lasting nail polish
    - Acrylic/Extensions: Artificial nail enhancements
    - Nail Art: Custom designs and decorations
    - Spa Services: Premium treatments with massage
""")

vn.train(documentation="""
    Booking Status Definitions:
    - scheduled: Appointment is confirmed and upcoming
    - completed: Customer showed up and service was provided
    - cancelled: Customer cancelled before appointment
    - no_show: Customer didn't show up for scheduled appointment
""")

vn.train(documentation="""
    Revenue Metrics:
    - total_amount: The final amount charged (after discounts, before tip)
    - discount_amount: Any promotions or discounts applied
    - tip_amount: Gratuity given to technician (not part of total_amount)
    - Only count bookings with status='completed' for revenue calculations
""")

vn.train(documentation="""
    Customer Retention:
    - New customer: First booking within last 30 days
    - Regular customer: 2+ visits in last 90 days
    - Lapsed customer: No visits in last 60 days
    - VIP customer: 10+ visits or $1000+ lifetime spend
""")
```

### Step 4: Train with SQL Examples

```python
import json

# Load the training questions
with open('training_data/nail-salon-pos/questions.json', 'r') as f:
    training_data = json.load(f)

# Train with each question-SQL pair
for item in training_data:
    vn.train(
        question=item['question'],
        sql=item['answer']
    )
```

### Step 5: Test Your Training

```python
# Ask questions and get SQL
sql = vn.generate_sql("What are our top 10 customers by spending?")
print(sql)

# Run the SQL and get results
df = vn.run_sql(sql)
print(df)

# Get the full response with visualization
vn.ask("What is our revenue trend for the last 6 months?")
```

## Alternative: Use Vanna's Auto-training Feature

If you already have a database, Vanna can automatically extract schema information:

```python
# Automatically train on all tables in your database
training_plan = vn.get_training_plan_generic(
    df=None  # Will introspect your connected database
)

# Review the training plan
print(training_plan)

# Execute the training plan
vn.train(plan=training_plan)
```

## Advanced: Custom Queries

For complex nail salon specific queries:

```python
# Train on advanced queries
vn.train(sql="""
    -- Calculate technician performance including tips
    SELECT 
        t.first_name,
        t.last_name,
        COUNT(b.booking_id) as total_appointments,
        SUM(b.total_amount) as service_revenue,
        SUM(b.tip_amount) as total_tips,
        AVG(b.tip_amount / NULLIF(b.total_amount, 0) * 100) as avg_tip_percentage
    FROM technicians t
    LEFT JOIN bookings b ON t.technician_id = b.technician_id
    WHERE b.status = 'completed'
        AND b.booking_date >= DATE_SUB(CURRENT_DATE, INTERVAL 1 MONTH)
    GROUP BY t.technician_id, t.first_name, t.last_name
    ORDER BY service_revenue DESC
""")

vn.train(sql="""
    -- Customer lifetime value with visit frequency
    SELECT 
        c.customer_id,
        c.first_name,
        c.last_name,
        COUNT(b.booking_id) as total_visits,
        SUM(b.total_amount) as lifetime_value,
        AVG(b.total_amount) as avg_transaction,
        MIN(b.booking_date) as first_visit,
        MAX(b.booking_date) as last_visit,
        DATEDIFF(MAX(b.booking_date), MIN(b.booking_date)) / NULLIF(COUNT(b.booking_id) - 1, 0) as avg_days_between_visits
    FROM customers c
    LEFT JOIN bookings b ON c.customer_id = b.customer_id
    WHERE b.status = 'completed'
    GROUP BY c.customer_id, c.first_name, c.last_name
    HAVING COUNT(b.booking_id) > 0
    ORDER BY lifetime_value DESC
""")
```

## Database Compatibility

Vanna supports multiple databases. Adjust the connection method:

### PostgreSQL
```python
vn.connect_to_postgres(
    host='localhost',
    dbname='nail_salon_pos',
    user='postgres',
    password='your_password',
    port=5432
)
```

### SQLite
```python
vn.connect_to_sqlite('nail_salon_pos.db')
```

### Snowflake
```python
vn.connect_to_snowflake(
    account='your_account',
    username='your_username',
    password='your_password',
    database='nail_salon_pos',
    warehouse='compute_wh'
)
```

## Tips for Better Results

1. **Train incrementally**: Start with basic queries and add more complex ones
2. **Use real examples**: Train with actual questions your staff asks
3. **Include edge cases**: Train on queries with date ranges, filters, aggregations
4. **Document business logic**: Explain calculations and business rules
5. **Test regularly**: Ask questions and verify SQL accuracy
6. **Iterative improvement**: When you find incorrect SQL, correct it and retrain

## Using Vanna in Your Application

### Streamlit App
```python
# Install: pip install vanna[streamlit]
import streamlit as st

# Create a simple interface
question = st.text_input("Ask a question about your salon data:")
if question:
    sql = vn.generate_sql(question)
    st.code(sql, language='sql')
    
    if st.button("Run Query"):
        df = vn.run_sql(sql)
        st.dataframe(df)
```

### Flask API
```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/ask', methods=['POST'])
def ask_question():
    question = request.json.get('question')
    sql = vn.generate_sql(question)
    results = vn.run_sql(sql)
    return jsonify({
        'sql': sql,
        'data': results.to_dict('records')
    })
```

## Maintenance

Regularly update your training data:

```python
# Remove outdated training data
vn.remove_training_data(id='specific_training_id')

# Add new queries as they're validated
vn.train(question="New question", sql="New SQL")
```

## Need Help?

- Documentation: https://vanna.ai/docs/
- Discord: https://discord.gg/qUZYKHremx
- GitHub: https://github.com/vanna-ai/vanna

