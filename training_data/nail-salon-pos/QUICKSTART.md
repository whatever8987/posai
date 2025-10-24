# Quick Start Guide: Vanna for Nail Salon POS

Get started with Vanna AI for your nail salon in 5 minutes!

## Installation

```bash
pip install vanna chromadb openai
```

## Basic Setup (3 Steps)

### 1. Initialize Vanna

```python
import os
from vanna.openai import OpenAI_Chat
from vanna.chromadb import ChromaDB_VectorStore

class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(self, config=config)

# Set your OpenAI API key
os.environ['OPENAI_API_KEY'] = 'sk-...'

vn = MyVanna(config={
    'api_key': os.environ['OPENAI_API_KEY'],
    'model': 'gpt-4',
    'path': './vanna_nail_salon'
})
```

### 2. Connect to Your Database

```python
# MySQL
vn.connect_to_mysql(
    host='localhost',
    dbname='nail_salon_pos',
    user='your_user',
    password='your_password',
    port=3306
)

# Or PostgreSQL
# vn.connect_to_postgres(...)

# Or SQLite
# vn.connect_to_sqlite('nail_salon.db')
```

### 3. Train on Your Schema

```python
# Option A: Auto-train from connected database
training_plan = vn.get_training_plan_generic(df=None)
vn.train(plan=training_plan)

# Option B: Manual training (recommended for better control)
vn.train(ddl="""
    CREATE TABLE customers (
        customer_id INT PRIMARY KEY,
        first_name VARCHAR(50),
        last_name VARCHAR(50),
        phone VARCHAR(20),
        email VARCHAR(100)
    )
""")

vn.train(ddl="""
    CREATE TABLE bookings (
        booking_id INT PRIMARY KEY,
        customer_id INT,
        technician_id INT,
        booking_date DATE,
        total_amount DECIMAL(10,2),
        status VARCHAR(20)
    )
""")
```

## Common Questions to Ask

Once trained, you can ask questions in plain English:

```python
# Revenue questions
sql = vn.generate_sql("What is our total revenue this month?")
df = vn.run_sql(sql)
print(df)

# Customer questions
vn.ask("Who are our top 10 customers by spending?")

# Technician questions
vn.ask("Which technician has the most appointments this week?")

# Service questions
vn.ask("What are our most popular services?")

# Inventory questions
vn.ask("Show me products with low stock")
```

## Example Workflow

Here's a complete example:

```python
# 1. Initialize
from vanna.openai import OpenAI_Chat
from vanna.chromadb import ChromaDB_VectorStore

class NailSalonVanna(ChromaDB_VectorStore, OpenAI_Chat):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(self, config=config)

vn = NailSalonVanna(config={
    'api_key': 'your-api-key',
    'model': 'gpt-4'
})

# 2. Connect
vn.connect_to_mysql(
    host='localhost',
    dbname='nail_salon_pos',
    user='root',
    password='password'
)

# 3. Train with examples
vn.train(documentation="""
    Status values: scheduled, completed, cancelled, no_show
    Only count 'completed' bookings for revenue.
""")

vn.train(
    question="What is today's revenue?",
    sql="""
        SELECT SUM(total_amount) as revenue
        FROM bookings
        WHERE DATE(booking_date) = CURRENT_DATE
        AND status = 'completed'
    """
)

# 4. Ask questions!
result = vn.ask("What is our revenue for this week?")
```

## Common Use Cases

### Daily Reports

```python
# Morning dashboard
questions = [
    "How many appointments do we have today?",
    "What is today's expected revenue?",
    "Which technicians are working today?",
    "Do we have any cancellations today?"
]

for question in questions:
    print(f"\n{question}")
    df = vn.run_sql(vn.generate_sql(question))
    print(df)
```

### Customer Insights

```python
# Customer analysis
vn.ask("Show me customers who haven't visited in 90 days")
vn.ask("What percentage of customers are repeat customers?")
vn.ask("Who are our VIP customers?")
vn.ask("Calculate customer lifetime value for top 20 customers")
```

### Technician Performance

```python
# Staff metrics
vn.ask("Show each technician's revenue for this month")
vn.ask("Which technician has the highest average ticket?")
vn.ask("Compare technician booking counts for last week")
vn.ask("Show average tips per technician")
```

### Service Analytics

```python
# Service trends
vn.ask("What are the top 10 most popular services?")
vn.ask("Which service category generates the most revenue?")
vn.ask("Show revenue by service category for this quarter")
vn.ask("What is the average number of services per appointment?")
```

### Inventory Management

```python
# Product tracking
vn.ask("Which products are below minimum stock level?")
vn.ask("What are the best-selling products this month?")
vn.ask("Show product sales revenue vs service revenue")
```

## Building a Simple Dashboard

### Streamlit App

```python
import streamlit as st

st.title("💅 Nail Salon Analytics")

# Question input
question = st.text_input("Ask a question about your salon:")

if question:
    # Generate SQL
    with st.spinner("Generating SQL..."):
        sql = vn.generate_sql(question)
    
    # Show SQL
    with st.expander("Generated SQL"):
        st.code(sql, language='sql')
    
    # Run and display results
    if st.button("Run Query"):
        df = vn.run_sql(sql)
        st.dataframe(df)
        
        # Try to create a chart
        if len(df.columns) == 2 and df.shape[0] > 0:
            st.bar_chart(df.set_index(df.columns[0]))
```

Run with: `streamlit run dashboard.py`

### Flask API

```python
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Initialize Vanna (once at startup)
vn = initialize_vanna()

@app.route('/api/ask', methods=['POST'])
def ask_question():
    data = request.json
    question = data.get('question')
    
    try:
        # Generate SQL
        sql = vn.generate_sql(question)
        
        # Run SQL
        df = vn.run_sql(sql)
        
        return jsonify({
            'success': True,
            'sql': sql,
            'data': df.to_dict('records'),
            'columns': list(df.columns)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/reports/daily', methods=['GET'])
def daily_report():
    reports = {}
    
    questions = {
        'appointments_today': "How many appointments do we have today?",
        'revenue_today': "What is today's total revenue?",
        'top_services': "What are today's most booked services?"
    }
    
    for key, question in questions.items():
        try:
            sql = vn.generate_sql(question)
            df = vn.run_sql(sql)
            reports[key] = df.to_dict('records')
        except Exception as e:
            reports[key] = {'error': str(e)}
    
    return jsonify(reports)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

## Tips for Better Results

### 1. Train with Real Questions
Collect actual questions your staff asks and train Vanna on them:

```python
real_questions = [
    "How much did Sarah make in tips last week?",
    "Show me all gel manicure appointments for tomorrow",
    "Which customers have birthdays this month?",
]

for q in real_questions:
    # Generate SQL
    sql = vn.generate_sql(q)
    # Review and correct if needed
    corrected_sql = "..."  # Your correction
    # Train with correct version
    vn.train(question=q, sql=corrected_sql)
```

### 2. Add Business Context

```python
vn.train(documentation="""
    Our salon has a loyalty program:
    - Bronze: 0-4 visits
    - Silver: 5-9 visits
    - Gold: 10-19 visits
    - Platinum: 20+ visits
    
    Gold and Platinum members get 10% discount automatically.
""")
```

### 3. Handle Complex Calculations

```python
vn.train(sql="""
    -- Technician performance with commission
    SELECT 
        t.first_name,
        t.last_name,
        COUNT(b.booking_id) as total_bookings,
        SUM(b.total_amount) as gross_revenue,
        SUM(b.total_amount * t.commission_rate / 100) as technician_commission,
        SUM(b.tip_amount) as total_tips
    FROM technicians t
    JOIN bookings b ON t.technician_id = b.technician_id
    WHERE b.status = 'completed'
        AND b.booking_date >= DATE_SUB(CURRENT_DATE, INTERVAL 1 MONTH)
    GROUP BY t.technician_id
""")
```

### 4. Test and Iterate

```python
# Always verify generated SQL
test_questions = [
    "What is our busiest hour of the day?",
    "Show me appointment no-show rate by day of week",
    "Compare this month's revenue to last month"
]

for q in test_questions:
    print(f"\nQ: {q}")
    sql = vn.generate_sql(q)
    print(f"SQL: {sql}")
    # Verify it's correct, if not, retrain
```

## Troubleshooting

### Issue: Generated SQL is incorrect

**Solution**: Train with the correct version

```python
question = "What is our cancellation rate?"
correct_sql = """
    SELECT 
        (COUNT(CASE WHEN status = 'cancelled' THEN 1 END) * 100.0 / COUNT(*)) as cancellation_rate
    FROM bookings
    WHERE booking_date >= DATE_SUB(CURRENT_DATE, INTERVAL 30 DAY)
"""
vn.train(question=question, sql=correct_sql)
```

### Issue: Vanna doesn't understand business terms

**Solution**: Add documentation

```python
vn.train(documentation="""
    Business terms:
    - 'Fill' or 'infill' = acrylic maintenance service
    - 'Soak-off' = removal of gel or acrylic nails
    - 'French tip' = classic nail art style with white tips
""")
```

### Issue: Slow response time

**Solution**: Use a faster model or cache common queries

```python
# Use GPT-3.5 instead of GPT-4 for faster responses
vn = MyVanna(config={
    'model': 'gpt-3.5-turbo',  # Faster
    'api_key': 'your-key'
})
```

## Next Steps

1. **Expand Training**: Add more example queries from your actual use cases
2. **Build Interface**: Create a Streamlit or web dashboard
3. **Automate Reports**: Schedule daily/weekly reports
4. **Add Validations**: Verify SQL before running
5. **Monitor Usage**: Track which questions are asked most
6. **Continuous Learning**: Retrain on successful queries

## Resources

- Full training script: `train_nail_salon.py`
- Example questions: `questions.json`
- Complete guide: `README.md`
- Official docs: https://vanna.ai/docs/

## Support

- GitHub Issues: https://github.com/vanna-ai/vanna/issues
- Discord: https://discord.gg/qUZYKHremx
- Documentation: https://vanna.ai/docs/

