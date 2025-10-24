# Using Vanna Locally with Ollama 🚀

**Run AI-powered SQL generation completely free on your local machine!**

## Why Ollama?

- ✅ **100% FREE** - No API costs, ever
- ✅ **100% PRIVATE** - Your data never leaves your computer
- ✅ **OFFLINE CAPABLE** - Works without internet after setup
- ✅ **NO LIMITS** - Generate unlimited queries

## Quick Setup (5 Minutes)

### 1. Install Ollama

**macOS:**
```bash
brew install ollama
# Or: curl -fsSL https://ollama.com/install.sh | sh
```

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows:**
Download from https://ollama.com/download/windows

### 2. Start Ollama & Get a Model

```bash
# Terminal 1: Start Ollama service
ollama serve

# Terminal 2: Download a model
ollama pull llama3.1

# Verify it's ready
ollama list
```

### 3. Install Python Packages

```bash
pip install vanna ollama chromadb
```

### 4. Run the Training Script

```bash
cd /Users/duyphan/vanna/training_data/nail-salon-pos
python train_nail_salon_ollama.py
```

That's it! 🎉

## Basic Usage

```python
from vanna.ollama import Ollama
from vanna.chromadb import ChromaDB_VectorStore

class MyVanna(ChromaDB_VectorStore, Ollama):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        Ollama.__init__(self, config=config)

# Initialize
vn = MyVanna(config={'model': 'llama3.1'})

# Connect to your database
vn.connect_to_mysql(
    host='localhost',
    dbname='nail_salon_pos',
    user='your_user',
    password='your_password'
)

# Ask questions in plain English!
vn.ask("What are our top 10 customers?")
vn.ask("What is today's revenue?")
vn.ask("Show me tomorrow's appointments")
```

## Recommended Models

Choose based on your available RAM:

| RAM Available | Recommended Model | Install Command |
|---------------|-------------------|-----------------|
| 8GB | llama3.2:3b | `ollama pull llama3.2:3b` |
| 16GB | llama3.1 | `ollama pull llama3.1` |
| 16GB+ | codellama | `ollama pull codellama` |
| 32GB+ | qwen2.5-coder | `ollama pull qwen2.5-coder` |

**Best for SQL**: `codellama` or `qwen2.5-coder`  
**Best all-around**: `llama3.1`  
**Fastest**: `llama3.2:3b`

## Performance Tips

### Keep Model in Memory
```python
config = {
    'model': 'llama3.1',
    'keep_alive': '-1'  # Keep loaded forever
}
```

### Increase Context Window
```python
config = {
    'model': 'llama3.1',
    'num_ctx': 8192  # More context = better understanding
}
```

### Make Responses Deterministic
```python
config = {
    'model': 'llama3.1',
    'options': {
        'temperature': 0.0  # 0 = most consistent, 1 = most creative
    }
}
```

## Files in This Package

- **OLLAMA_QUICKSTART.md** ⚡ - 5-minute setup guide
- **OLLAMA_SETUP.md** 📖 - Complete configuration guide
- **train_nail_salon_ollama.py** 🎓 - Automated training script
- **example_usage.py** 💡 - Code examples
- **questions.json** 📊 - 20 pre-written training examples
- **sample_schema.sql** 🗄️ - Test database

## Common Questions

### Q: How much RAM do I need?
**A:** Minimum 8GB. 16GB recommended for best experience.

### Q: Can I use GPU acceleration?
**A:** Yes! Ollama automatically uses NVIDIA GPUs (CUDA) or Apple Silicon (Metal) if available.

### Q: Which model is best for SQL?
**A:** Try `codellama` or `qwen2.5-coder` - they're optimized for code generation.

### Q: How accurate is it compared to GPT-4?
**A:** Ollama models are ~85-90% accurate vs GPT-4's ~95%. Good enough for most use cases!

### Q: Can I switch between models?
**A:** Yes! Just change the `model` parameter in your config.

## Troubleshooting

### "Connection refused" Error
```bash
# Make sure Ollama is running:
ollama serve
```

### Model Not Found
```bash
# Download it:
ollama pull llama3.1
ollama list  # Verify
```

### Out of Memory
```bash
# Use smaller model:
ollama pull llama3.2:3b

# Then in code:
config = {'model': 'llama3.2:3b'}
```

### Slow Responses
1. Keep model loaded: `'keep_alive': '-1'`
2. Use smaller model: `llama3.2:3b`
3. Reduce context: `'num_ctx': 2048`
4. Close other applications

## Example Workflow

### 1. Test Connection
```bash
ollama list  # See available models
ollama run llama3.1 "Hello"  # Quick test
```

### 2. Train Vanna
```bash
python train_nail_salon_ollama.py
```

### 3. Use in Your App
```python
vn = MyVanna(config={'model': 'llama3.1'})
vn.connect_to_mysql(...)

# Daily revenue
sql = vn.generate_sql("What is today's revenue?")
df = vn.run_sql(sql)
print(df)
```

## Building a Dashboard

### Streamlit App
```python
import streamlit as st

st.title("💅 Nail Salon Analytics")

@st.cache_resource
def get_vanna():
    vn = MyVanna(config={'model': 'llama3.1', 'keep_alive': '-1'})
    vn.connect_to_mysql(...)
    return vn

vn = get_vanna()
question = st.text_input("Ask a question:")

if question:
    sql = vn.generate_sql(question)
    st.code(sql)
    
    df = vn.run_sql(sql)
    st.dataframe(df)
```

Run with: `streamlit run app.py`

## Comparing to OpenAI

| Feature | Ollama | OpenAI |
|---------|--------|--------|
| Cost | FREE | $0.01-0.03/query |
| Privacy | 100% Local | Cloud |
| Speed | 2-10s | 1-3s |
| Accuracy | 85-90% | 95%+ |
| Setup | Medium | Easy |

**Use Ollama if:**
- You want zero costs
- Privacy is important
- You have 8GB+ RAM

**Use OpenAI if:**
- You want best accuracy
- You prefer simple setup
- Cost is not a concern

## Advanced Configuration

### Custom System Prompt
```python
class MyVanna(ChromaDB_VectorStore, Ollama):
    def get_sql_prompt(self, question, **kwargs):
        prompt = super().get_sql_prompt(question, **kwargs)
        # Add custom instructions
        custom = """
        IMPORTANT RULES:
        - Always filter bookings by status='completed' for revenue
        - Use proper MySQL date functions
        """
        prompt.insert(1, self.system_message(custom))
        return prompt
```

### Multiple Models
```python
# Try different models for comparison
models = ['llama3.1', 'codellama', 'qwen2.5-coder']

for model in models:
    vn = MyVanna(config={'model': model})
    sql = vn.generate_sql("Your question")
    print(f"{model}: {sql}")
```

## Next Steps

1. ✅ Complete setup (above)
2. ✅ Run training script
3. ✅ Try example questions
4. ✅ Connect your real database
5. ✅ Build your dashboard
6. ✅ Share with your team!

## Resources

- **Ollama Website**: https://ollama.com
- **Available Models**: https://ollama.com/library
- **Vanna Docs**: https://vanna.ai/docs/
- **This Package**: See INDEX.md

## Support

- **Ollama Discord**: https://discord.gg/ollama
- **Vanna Discord**: https://discord.gg/qUZYKHremx
- **Issues**: https://github.com/vanna-ai/vanna/issues

---

**Enjoy free, private AI for your nail salon! 💅✨**

Made with ❤️ for nail salon owners who want powerful analytics without the cloud costs.

