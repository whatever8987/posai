y# What to Do After Training 🎉

Your Vanna model is now trained! Here's what you can do next.

## ✅ Training Complete!

Your trained model is saved in: `./chroma_db_nail_salon/`

This contains all your:
- ✅ Database schema knowledge
- ✅ Business rules and terminology
- ✅ 20+ example question-SQL pairs
- ✅ Vector embeddings for semantic search

## 🚀 Option 1: Quick Test (Recommended First Step)

Run the interactive script:

```bash
python use_vanna.py
```

**What it does:**
- Loads your trained model
- Shows example questions
- Lets you ask custom questions
- Generates SQL (no database needed yet)

**Perfect for:**
- Testing the model
- Seeing what SQL it generates
- Learning what questions work well

---

## 💬 Option 2: Interactive Q&A

```python
from vanna.ollama import Ollama
from vanna.chromadb import ChromaDB_VectorStore

class MyVanna(ChromaDB_VectorStore, Ollama):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        Ollama.__init__(self, config=config)

# Load trained model
vn = MyVanna(config={
    'model': 'qwen2.5:7b',
    'path': './chroma_db_nail_salon'
})

# Ask questions!
sql = vn.generate_sql("What are our top 10 customers?")
print(sql)
```

---

## 🗄️ Option 3: Connect Your Real Database

Once you're happy with the SQL quality, connect your actual database:

### MySQL
```python
vn.connect_to_mysql(
    host='localhost',
    dbname='nail_salon_pos',
    user='your_user',
    password='your_password',
    port=3306
)

# Now you can run queries
df = vn.run_sql(sql)
print(df)
```

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

---

## 🎨 Option 4: Build a Dashboard

### Quick Streamlit Dashboard (Easiest!)

```bash
# Install Streamlit
pip install streamlit plotly

# Run the pre-built dashboard
streamlit run dashboard.py
```

**Opens in your browser with:**
- 💬 Natural language query interface
- 📊 Auto-generated visualizations
- 📝 SQL editor
- 📈 Business dashboard

**Perfect for:**
- End users who don't know SQL
- Daily business reporting
- Team-wide access

---

## 📋 Common Questions You Can Ask

### Revenue Questions
```python
vn.ask("What is our total revenue this month?")
vn.ask("Show daily revenue for the last 7 days")
vn.ask("Compare this month's revenue to last month")
vn.ask("What is our average transaction value?")
```

### Customer Questions
```python
vn.ask("Who are our top 10 customers by spending?")
vn.ask("How many new customers this month?")
vn.ask("Which customers haven't visited in 60 days?")
vn.ask("What is our customer retention rate?")
```

### Technician Questions
```python
vn.ask("Which technician has the most bookings this week?")
vn.ask("Show each technician's revenue for this month")
vn.ask("What is the average tip per technician?")
vn.ask("Who is our busiest technician?")
```

### Service Questions
```python
vn.ask("What are our 5 most popular services?")
vn.ask("Which service generates the most revenue?")
vn.ask("How many gel manicures did we do this week?")
vn.ask("What is the average price per service?")
```

### Operational Questions
```python
vn.ask("How many appointments do we have today?")
vn.ask("Show tomorrow's schedule")
vn.ask("What is our cancellation rate this month?")
vn.ask("What are our busiest days of the week?")
```

---

## 🔧 Advanced Options

### Option 5: Build a REST API

```python
from flask import Flask, request, jsonify

app = Flask(__name__)
vn = MyVanna(config={'model': 'qwen2.5:7b', 'path': './chroma_db_nail_salon'})
vn.connect_to_mysql(...)

@app.route('/ask', methods=['POST'])
def ask():
    question = request.json['question']
    sql = vn.generate_sql(question)
    results = vn.run_sql(sql)
    return jsonify({
        'sql': sql,
        'data': results.to_dict('records')
    })

app.run(port=5000)
```

### Option 6: Scheduled Reports

```python
import schedule
import time

def daily_report():
    questions = [
        "What was yesterday's revenue?",
        "How many appointments do we have today?",
        "Which customers need follow-up calls?"
    ]
    
    for q in questions:
        sql = vn.generate_sql(q)
        df = vn.run_sql(sql)
        # Send email or save to file
        print(f"{q}\n{df}\n")

# Run every day at 8 AM
schedule.every().day.at("08:00").do(daily_report)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### Option 7: Integrate with Your POS

```python
# In your existing POS application
from your_vanna_module import vn

# Add AI insights to your app
def get_customer_insights(customer_id):
    question = f"Show me purchase history and trends for customer {customer_id}"
    sql = vn.generate_sql(question)
    return vn.run_sql(sql)

# Add to your dashboard
insights = get_customer_insights(123)
display_insights(insights)
```

---

## 🎯 Next Steps Checklist

- [ ] **Test the model** with `python use_vanna.py`
- [ ] **Connect your database** and run real queries
- [ ] **Build a dashboard** with `streamlit run dashboard.py`
- [ ] **Train your team** on what questions to ask
- [ ] **Add more examples** as you find what works
- [ ] **Deploy** to production environment

---

## 💡 Tips for Best Results

### 1. Start Simple
Begin with straightforward questions before complex ones:
- ✅ "What is today's revenue?"
- ⚠️ "Show me a cohort analysis of customer retention by service type"

### 2. Add More Training
If a question doesn't work well, train it:
```python
vn.train(
    question="Your question",
    sql="Correct SQL for this question"
)
```

### 3. Be Specific
- ❌ "Show me customers"
- ✅ "Show me top 10 customers by spending this month"

### 4. Use Business Terms
The model understands your nail salon terminology:
- "gel manicure", "acrylic fill", "spa pedicure"
- "completed bookings", "cancelled", "no-show"
- "revenue", "tips", "technician commission"

### 5. Iterate and Improve
- Test different phrasings
- Save queries that work well
- Retrain on corrections
- Build a library of common queries

---

## 📊 Example Daily Workflow

### Morning (5 minutes)
```bash
streamlit run dashboard.py
```
- Check today's appointments
- Review yesterday's revenue
- See which technicians are busy

### Throughout the Day (as needed)
```python
# Quick queries
vn.ask("How many walk-ins today?")
vn.ask("Do we have openings this afternoon?")
vn.ask("What's our revenue so far today?")
```

### End of Day (10 minutes)
```python
# Daily reports
vn.ask("What was today's total revenue?")
vn.ask("How many no-shows did we have?")
vn.ask("Which services were most popular today?")
```

---

## 🔄 Maintenance

### Keep Model Updated
As your business evolves, add new training:
```python
# New service added
vn.train(ddl="ALTER TABLE services ADD COLUMN...")

# New business rule
vn.train(documentation="New VIP tier: 20+ visits gets 15% discount")

# New common question
vn.train(
    question="Show VIP customers",
    sql="SELECT * FROM customers WHERE total_visits >= 20"
)
```

### Monitor Quality
- Review generated SQL regularly
- Correct and retrain on mistakes
- Keep a log of common questions

---

## 🆘 Troubleshooting

### SQL is incorrect
```python
# Fix it and retrain
correct_sql = "YOUR CORRECTED SQL"
vn.train(question="the question", sql=correct_sql)
```

### Model is slow
```python
# Use lighter model or keep in memory
config = {
    'model': 'llama3.2:3b',  # Faster
    'keep_alive': '-1'  # Keep loaded
}
```

### Can't connect to database
```python
# Test connection separately
import mysql.connector
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='password'
)
```

---

## 🎓 Resources

- **use_vanna.py** - Interactive testing script
- **dashboard.py** - Streamlit dashboard
- **example_usage.py** - More code examples
- **OLLAMA_SETUP.md** - Ollama configuration
- **questions.json** - Training examples

---

## 🎉 You're Ready!

Your AI assistant is trained and ready to help you understand your nail salon business better. Start with simple questions and build from there!

**Need help?** Check the Discord: https://discord.gg/qUZYKHremx

---

**Happy querying! 💅✨**

