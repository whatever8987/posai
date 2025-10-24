# Using Vanna with Ollama (Local Setup)

Complete guide for running Vanna locally with Ollama - no cloud API needed, 100% private!

## Why Ollama?

✅ **Completely Free** - No API costs  
✅ **100% Private** - All data stays on your machine  
✅ **No Internet Required** - Works offline after setup  
✅ **Fast** - Direct local inference  
✅ **Multiple Models** - Choose from Llama, Mistral, CodeLlama, etc.

## Prerequisites

- **RAM**: At least 8GB (16GB+ recommended)
- **Storage**: 4-10GB per model
- **OS**: macOS, Linux, or Windows

## Step 1: Install Ollama

### macOS
```bash
# Download and install from website
curl -fsSL https://ollama.com/install.sh | sh

# Or use Homebrew
brew install ollama
```

### Linux
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Windows
Download installer from: https://ollama.com/download/windows

## Step 2: Start Ollama Service

```bash
# Start Ollama server (runs in background)
ollama serve
```

Keep this terminal open, or run it as a service.

## Step 3: Pull a Model

Choose a model based on your hardware:

```bash
# Recommended: Llama 3.1 8B (requires ~8GB RAM)
ollama pull llama3.1

# Alternative: Llama 3.2 3B (lighter, requires ~4GB RAM)
ollama pull llama3.2

# For SQL-specific tasks: CodeLlama (optimized for code)
ollama pull codellama

# Fast and efficient: Mistral
ollama pull mistral

# List all downloaded models
ollama list
```

### Model Recommendations for Nail Salon POS

| Model | Size | RAM Needed | Best For |
|-------|------|------------|----------|
| `llama3.1` | 4.7GB | 8GB | Best overall accuracy |
| `llama3.2:3b` | 2GB | 4GB | Faster, good for simple queries |
| `codellama` | 3.8GB | 8GB | SQL generation |
| `mistral` | 4.1GB | 8GB | Fast and accurate |
| `qwen2.5-coder` | 4.7GB | 8GB | Great for SQL |

## Step 4: Install Python Packages

```bash
pip install vanna ollama chromadb
```

## Step 5: Initialize Vanna with Ollama

Create a file `vanna_ollama.py`:

```python
from vanna.ollama import Ollama
from vanna.chromadb import ChromaDB_VectorStore

class NailSalonVanna(ChromaDB_VectorStore, Ollama):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        Ollama.__init__(self, config=config)

# Initialize with your chosen model
vn = NailSalonVanna(config={
    'model': 'llama3.1',  # or 'codellama', 'mistral', etc.
    'ollama_host': 'http://localhost:11434',
    'num_ctx': 4096,  # Context window size
    'path': './chroma_db_nail_salon'  # Local vector DB storage
})

print("✓ Vanna initialized with Ollama!")
```

## Step 6: Connect to Your Database

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

## Step 7: Train Vanna

Use the provided training script:

```bash
python train_nail_salon_ollama.py
```

Or manually train:

```python
# Train with DDL
vn.train(ddl="""
    CREATE TABLE customers (
        customer_id INT PRIMARY KEY,
        first_name VARCHAR(50),
        last_name VARCHAR(50),
        phone VARCHAR(20)
    )
""")

# Train with documentation
vn.train(documentation="""
    Booking status values: scheduled, completed, cancelled, no_show.
    Only count 'completed' bookings for revenue calculations.
""")

# Train with examples
vn.train(
    question="What is our revenue this month?",
    sql="SELECT SUM(total_amount) FROM bookings WHERE status='completed' AND MONTH(booking_date)=MONTH(CURRENT_DATE)"
)
```

## Step 8: Ask Questions!

```python
# Generate SQL
sql = vn.generate_sql("Who are our top 10 customers by spending?")
print(sql)

# Run SQL and get results
df = vn.run_sql(sql)
print(df)

# Or use ask() for full response
vn.ask("What is today's revenue?")
```

## Complete Example

Here's a full working example:

```python
from vanna.ollama import Ollama
from vanna.chromadb import ChromaDB_VectorStore

# 1. Create custom class
class NailSalonVanna(ChromaDB_VectorStore, Ollama):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        Ollama.__init__(self, config=config)

# 2. Initialize
vn = NailSalonVanna(config={
    'model': 'llama3.1',
    'num_ctx': 4096
})

# 3. Connect to database
vn.connect_to_mysql(
    host='localhost',
    dbname='nail_salon_pos',
    user='root',
    password='password'
)

# 4. Train (first time only)
vn.train(ddl="""
    CREATE TABLE bookings (
        booking_id INT PRIMARY KEY,
        customer_id INT,
        booking_date DATE,
        total_amount DECIMAL(10,2),
        status VARCHAR(20)
    )
""")

vn.train(
    question="What is today's revenue?",
    sql="SELECT SUM(total_amount) FROM bookings WHERE DATE(booking_date) = CURRENT_DATE AND status='completed'"
)

# 5. Ask questions!
result = vn.ask("Show me today's appointments")
```

## Configuration Options

### Performance Tuning

```python
config = {
    'model': 'llama3.1',
    'ollama_host': 'http://localhost:11434',
    
    # Context window (higher = more context, slower)
    'num_ctx': 4096,  # Default: 2048, Max: depends on model
    
    # Keep model loaded in memory (faster repeated queries)
    'keep_alive': '5m',  # Keep for 5 minutes, or '-1' for forever
    
    # Temperature (lower = more deterministic)
    'options': {
        'temperature': 0.1,  # 0-1, lower = more consistent
        'top_p': 0.9,
        'top_k': 40
    },
    
    # Timeout for slow queries
    'ollama_timeout': 240.0  # seconds
}

vn = NailSalonVanna(config=config)
```

### Optimize for Speed

```python
# Use lighter model
config = {
    'model': 'llama3.2:3b',  # Smaller, faster
    'num_ctx': 2048,
    'keep_alive': '-1',  # Keep in memory
    'options': {
        'temperature': 0.1,
        'num_predict': 500  # Limit output length
    }
}
```

### Optimize for Accuracy

```python
# Use larger model with more context
config = {
    'model': 'codellama',  # SQL-optimized
    'num_ctx': 8192,  # Larger context
    'options': {
        'temperature': 0.0,  # Most deterministic
        'top_p': 1.0
    }
}
```

## Testing Ollama Connection

Test if Ollama is working:

```python
import ollama

# List available models
models = ollama.list()
print("Available models:", models)

# Test a simple query
response = ollama.chat(
    model='llama3.1',
    messages=[{'role': 'user', 'content': 'Say hello'}]
)
print(response['message']['content'])
```

## Troubleshooting

### Issue: "Connection refused" error

**Solution:** Make sure Ollama service is running
```bash
# Start Ollama in terminal
ollama serve

# Or check if running
ps aux | grep ollama
```

### Issue: Model not found

**Solution:** Pull the model first
```bash
ollama pull llama3.1
ollama list  # Verify it's downloaded
```

### Issue: Out of memory

**Solutions:**
1. Use a smaller model: `llama3.2:3b` instead of `llama3.1`
2. Close other applications
3. Reduce `num_ctx`: Use 2048 instead of 4096

### Issue: Slow response times

**Solutions:**
1. Use `keep_alive: '-1'` to keep model in memory
2. Use a smaller model
3. Reduce `num_ctx`
4. Add more RAM to your system

### Issue: Incorrect SQL generated

**Solutions:**
1. Use `codellama` or `qwen2.5-coder` (better at SQL)
2. Train with more examples
3. Lower temperature to 0.0 for consistency
4. Add more context with `num_ctx: 8192`

## Comparing Models

Test different models to see which works best:

```python
models = ['llama3.1', 'codellama', 'mistral', 'qwen2.5-coder']
test_question = "What are the top 10 customers by spending?"

for model_name in models:
    print(f"\n=== Testing {model_name} ===")
    vn = NailSalonVanna(config={'model': model_name})
    
    # Train first (once per model)
    # ... training code ...
    
    # Generate SQL
    sql = vn.generate_sql(test_question)
    print(f"Generated: {sql}")
```

## Building a Dashboard with Ollama

### Streamlit App

```python
import streamlit as st
from vanna.ollama import Ollama
from vanna.chromadb import ChromaDB_VectorStore

class MyVanna(ChromaDB_VectorStore, Ollama):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        Ollama.__init__(self, config=config)

@st.cache_resource
def get_vanna():
    vn = MyVanna(config={
        'model': 'llama3.1',
        'keep_alive': '-1'  # Keep loaded
    })
    vn.connect_to_mysql(...)
    return vn

st.title("💅 Nail Salon Analytics (Local AI)")

vn = get_vanna()
question = st.text_input("Ask a question:")

if question:
    with st.spinner("Generating SQL with local AI..."):
        sql = vn.generate_sql(question)
    
    st.code(sql, language='sql')
    
    if st.button("Run Query"):
        df = vn.run_sql(sql)
        st.dataframe(df)
```

Run with: `streamlit run app.py`

## Hardware Requirements

### Minimum Setup
- **CPU**: Any modern processor
- **RAM**: 8GB
- **Storage**: 10GB
- **Model**: llama3.2:3b or mistral

### Recommended Setup
- **CPU**: 4+ cores
- **RAM**: 16GB
- **Storage**: 20GB
- **Model**: llama3.1, codellama, or qwen2.5-coder

### Optimal Setup
- **CPU**: 8+ cores or GPU (NVIDIA with CUDA)
- **RAM**: 32GB
- **Storage**: 50GB
- **Model**: llama3.1:70b (if you have 64GB+ RAM)

## GPU Acceleration (Optional)

If you have an NVIDIA GPU:

```bash
# Ollama automatically uses GPU if available
# Verify GPU is being used:
nvidia-smi  # Should show ollama process

# For Apple Silicon Macs, Metal is used automatically
```

## Comparison: Ollama vs OpenAI

| Feature | Ollama (Local) | OpenAI (Cloud) |
|---------|----------------|----------------|
| **Cost** | Free | ~$0.01-0.03 per query |
| **Privacy** | 100% private | Data sent to cloud |
| **Internet** | Not required | Required |
| **Speed** | 2-10s (depends on hardware) | 1-3s |
| **Accuracy** | Good (85-90%) | Excellent (95%+) |
| **Setup** | More complex | Very simple |
| **Maintenance** | Update models manually | Automatic |

## Best Practices

1. **Choose the right model**: Start with `llama3.1`, switch to `codellama` if SQL quality is low
2. **Keep model loaded**: Use `keep_alive: '-1'` for faster repeated queries
3. **Train well**: More training examples = better results
4. **Monitor memory**: Watch RAM usage, especially with large models
5. **Test queries**: Always verify generated SQL before running on production

## Advanced: Custom System Prompts

Improve SQL generation with custom prompts:

```python
class MyVanna(ChromaDB_VectorStore, Ollama):
    def get_sql_prompt(self, question, **kwargs):
        prompt = super().get_sql_prompt(question, **kwargs)
        # Add custom instructions
        custom_instruction = """
        IMPORTANT: 
        - Always filter bookings by status='completed' for revenue
        - Use proper date formatting for MySQL
        - Include table aliases for clarity
        """
        prompt.insert(1, self.system_message(custom_instruction))
        return prompt
```

## Next Steps

1. ✅ Install Ollama and pull a model
2. ✅ Run `train_nail_salon_ollama.py`
3. ✅ Test with sample questions
4. ✅ Compare models to find the best one
5. ✅ Build your dashboard
6. ✅ Deploy locally for your team

## Resources

- **Ollama Website**: https://ollama.com
- **Ollama Models**: https://ollama.com/library
- **Vanna Docs**: https://vanna.ai/docs/
- **GitHub**: https://github.com/vanna-ai/vanna

## Support

- Ollama Discord: https://discord.gg/ollama
- Vanna Discord: https://discord.gg/qUZYKHremx

---

**Enjoy free, private AI for your nail salon! 💅🤖**

