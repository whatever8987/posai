# Nail Salon POS - Vanna AI Training Package

Complete guide and training materials for using Vanna AI with a nail salon point-of-sale system.

## 📁 What's Included

### Choose Your Setup:
- **☁️ Cloud (OpenAI)**: Easy setup, best accuracy, costs ~$0.01-0.03/query
- **💻 Local (Ollama)**: Free, private, works offline, needs 8GB+ RAM

---

### 1. **QUICKSTART.md** ⭐ START HERE (OpenAI)
- 5-minute setup guide with OpenAI
- Basic examples and common questions
- Simple dashboard code (Streamlit & Flask)
- Perfect for getting started quickly

### 1b. **OLLAMA_QUICKSTART.md** ⚡ START HERE (Local/Free)
- 5-minute setup with Ollama (local AI)
- 100% free and private
- No API keys needed
- Works offline after setup

### 2. **README.md** - Complete Guide (OpenAI)
- Detailed step-by-step training instructions
- All training methods explained (DDL, documentation, SQL examples)
- Database connection examples for MySQL, PostgreSQL, SQLite, Snowflake
- Advanced queries and best practices
- Maintenance tips

### 2b. **OLLAMA_SETUP.md** - Complete Local Guide
- Comprehensive Ollama setup and configuration
- Model selection and optimization
- Hardware requirements
- Performance tuning
- Troubleshooting guide

### 3. **train_nail_salon.py** - Training Script (OpenAI)
- Ready-to-use Python script
- Trains all schemas, documentation, and examples
- Just set your OPENAI_API_KEY and run
- Includes testing functionality
- Usage: `python train_nail_salon.py`

### 3b. **train_nail_salon_ollama.py** - Training Script (Local)
- Local training with Ollama
- No API keys required
- Tests Ollama connection automatically
- Downloads models if needed
- Usage: `python train_nail_salon_ollama.py`

### 4. **questions.json** - 20 Training Examples
- Pre-written question-SQL pairs
- Covers common nail salon queries:
  - Revenue analysis
  - Customer insights
  - Technician performance
  - Service popularity
  - Inventory management
- Used by both training scripts automatically

### 5. **sample_schema.sql** - Test Database
- Complete database schema for nail salon
- Sample data included (customers, bookings, services, etc.)
- Ready to import and test
- Usage: `mysql -u root -p nail_salon_pos < sample_schema.sql`

## 🚀 Quick Start

### Option A: Cloud/OpenAI (Best Accuracy)

```bash
# 1. Install
pip install vanna chromadb openai

# 2. Set API key
export OPENAI_API_KEY='your-openai-api-key-here'

# 3. Train
cd training_data/nail-salon-pos
python train_nail_salon.py
```

### Option B: Local/Ollama (Free & Private) ⭐ RECOMMENDED

```bash
# 1. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Get model
ollama serve  # Keep running in one terminal
ollama pull llama3.1  # In another terminal

# 3. Install Python packages
pip install vanna ollama chromadb

# 4. Train
cd training_data/nail-salon-pos
python train_nail_salon_ollama.py
```

That's it! Now you can ask questions in plain English.

## 📖 Learning Path

**For Beginners (Local/Free):**
1. Read `OLLAMA_QUICKSTART.md` (5 minutes)
2. Set up a test database with `sample_schema.sql` (5 minutes)
3. Run `train_nail_salon_ollama.py` (5 minutes)
4. Start asking questions!

**For Beginners (Cloud/OpenAI):**
1. Read `QUICKSTART.md` (10 minutes)
2. Set up a test database with `sample_schema.sql` (5 minutes)
3. Run `train_nail_salon.py` (5 minutes)
4. Start asking questions!

**For Advanced Users:**
1. Read `README.md` or `OLLAMA_SETUP.md` for comprehensive understanding
2. Customize training script for your specific schema
3. Add your own questions to `questions.json`
4. Integrate into your existing application

## 💡 Common Use Cases

### Daily Operations
```python
vn.ask("How many appointments do we have today?")
vn.ask("What is today's expected revenue?")
vn.ask("Show me today's schedule by technician")
```

### Business Analytics
```python
vn.ask("What are our top 10 customers by spending?")
vn.ask("Which services generate the most revenue?")
vn.ask("What is our customer retention rate?")
```

### Staff Management
```python
vn.ask("Show each technician's revenue for this month")
vn.ask("Which technician has the highest average tips?")
vn.ask("Compare technician booking counts this week vs last week")
```

### Inventory
```python
vn.ask("Show me products below minimum stock level")
vn.ask("What are the top 5 best-selling products?")
vn.ask("Calculate product inventory value")
```

## 🗃️ Database Schema Overview

The sample schema includes these tables:

- **customers** - Customer information and contact details
- **technicians** - Staff members and their specialties
- **services** - Available services with pricing
- **bookings** - Appointments and transactions
- **booking_services** - Services per appointment (many-to-many)
- **products** - Retail inventory
- **product_sales** - Product transaction history

## 🤔 OpenAI vs Ollama - Which to Choose?

| Feature | Ollama (Local) | OpenAI (Cloud) |
|---------|----------------|----------------|
| **Cost** | ✅ FREE | ❌ ~$0.01-0.03/query |
| **Privacy** | ✅ 100% Local | ⚠️ Data sent to cloud |
| **Internet** | ✅ Not required | ❌ Required |
| **Setup** | ⚠️ More steps | ✅ Very simple |
| **Speed** | ⚠️ 2-10s (depends on hardware) | ✅ 1-3s |
| **Accuracy** | ✅ Good (85-90%) | ✅ Excellent (95%+) |
| **Hardware** | ⚠️ Needs 8GB+ RAM | ✅ None |

**Choose Ollama if:**
- You want zero ongoing costs
- Privacy is critical
- You have decent hardware (8GB+ RAM)
- You're okay with slightly longer response times

**Choose OpenAI if:**
- You want the best accuracy
- You prefer simple setup
- You don't mind small API costs
- You need the fastest responses

## 🔧 Customization

### For Your Existing Database

1. Update the `train_database_schema()` function in `train_nail_salon.py` with your actual table structures
2. Modify business documentation in `train_business_documentation()` to match your terminology
3. Add your specific queries to `questions.json`
4. Update database connection details

### Adding New Training Data

```python
# Add new question-SQL pair
vn.train(
    question="Your new question here",
    sql="Your SQL query here"
)

# Add business documentation
vn.train(documentation="Your business rules here")

# Add table schema
vn.train(ddl="CREATE TABLE ... ")
```

## 📊 Building Dashboards

### Option 1: Streamlit (Easiest)
See example in `QUICKSTART.md` - creates interactive web interface in minutes

### Option 2: Flask API
See example in `QUICKSTART.md` - builds REST API for integration

### Option 3: Jupyter Notebook
Perfect for data analysis and reporting

### Option 4: Custom Frontend
Use Vanna API from any JavaScript/React/Vue app

## ⚙️ Configuration Options

### Different LLMs
```python
# OpenAI GPT-4 (recommended)
config = {'api_key': 'sk-...', 'model': 'gpt-4'}

# OpenAI GPT-3.5 (faster, cheaper)
config = {'api_key': 'sk-...', 'model': 'gpt-3.5-turbo'}

# Or use other providers: Anthropic, Gemini, Ollama, etc.
```

### Different Vector Databases
```python
# ChromaDB (default, local)
from vanna.chromadb import ChromaDB_VectorStore

# Pinecone (cloud-hosted)
from vanna.pinecone import Pinecone_VectorStore

# PostgreSQL pgvector
from vanna.pgvector import PGVector_VectorStore
```

### Different Databases
```python
# MySQL
vn.connect_to_mysql(host, dbname, user, password)

# PostgreSQL
vn.connect_to_postgres(host, dbname, user, password)

# SQLite
vn.connect_to_sqlite('database.db')

# Snowflake
vn.connect_to_snowflake(account, username, password, database)
```

## 📈 Expected Results

After training, Vanna should be able to:
- ✅ Answer 80-90% of common business questions accurately
- ✅ Generate complex SQL with JOINs and aggregations
- ✅ Handle date ranges and time-based queries
- ✅ Understand business terminology specific to nail salons
- ✅ Provide results in seconds

## 🔍 Troubleshooting

### Problem: "Module not found"
**Solution:** Install required packages
```bash
pip install vanna chromadb openai
```

### Problem: "API key not set"
**Solution:** Set environment variable
```bash
export OPENAI_API_KEY='your-key'
# or in Python: os.environ['OPENAI_API_KEY'] = 'your-key'
```

### Problem: Generated SQL is incorrect
**Solution:** Train with correct version
```python
vn.train(question="the question", sql="correct SQL")
```

### Problem: Can't connect to database
**Solution:** Check connection details and permissions
```python
# Test connection separately first
import mysql.connector
conn = mysql.connector.connect(host='localhost', user='root', password='pwd')
```

## 📚 Resources

- **Official Vanna Docs:** https://vanna.ai/docs/
- **GitHub Repository:** https://github.com/vanna-ai/vanna
- **Discord Community:** https://discord.gg/qUZYKHremx
- **Example Apps:** 
  - Streamlit: https://github.com/vanna-ai/vanna-streamlit
  - Flask: https://github.com/vanna-ai/vanna-flask

## 🎯 Next Steps

1. ✅ Read `QUICKSTART.md`
2. ✅ Run `train_nail_salon.py`
3. ✅ Test with sample questions
4. ✅ Connect to your actual database
5. ✅ Customize training data for your needs
6. ✅ Build a dashboard interface
7. ✅ Deploy for your team

## 💬 Support

Need help? Here's what to do:
1. Check the README.md for detailed explanations
2. Review examples in QUICKSTART.md
3. Search Vanna documentation
4. Ask in the Discord community
5. Open an issue on GitHub

## 📝 License

This training package is part of the Vanna project (MIT License).
You're free to use, modify, and distribute for your nail salon business.

---

**Happy querying! 💅✨**

Created for nail salon owners and developers who want to leverage AI for business intelligence.

