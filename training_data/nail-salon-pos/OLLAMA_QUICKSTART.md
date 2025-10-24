# Ollama Quick Start - 5 Minutes ⚡

Get Vanna running locally with Ollama in 5 minutes!

## Step 1: Install Ollama (2 minutes)

```bash
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Or download from: https://ollama.com
```

## Step 2: Get a Model (1 minute)

```bash
# Start Ollama (in a new terminal, keep it running)
ollama serve

# In another terminal, download a model
ollama pull llama3.1
```

## Step 3: Install Python Packages (1 minute)

```bash
pip install vanna ollama chromadb
```

## Step 4: Run the Training Script (1 minute)

```bash
cd training_data/nail-salon-pos
python train_nail_salon_ollama.py
```

## Step 5: Start Asking Questions! ✨

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
    user='root',
    password='password'
)

# Ask questions!
vn.ask("What are our top 10 customers?")
vn.ask("What is today's revenue?")
vn.ask("Show me tomorrow's appointments")
```

## That's It! 🎉

You now have:
- ✅ Free AI running locally
- ✅ 100% private (no data leaves your machine)
- ✅ No API costs
- ✅ Works offline

## Common Issues

### "Connection refused"
```bash
# Make sure Ollama is running:
ollama serve
```

### "Model not found"
```bash
# Download the model:
ollama pull llama3.1
```

### "Out of memory"
```bash
# Use a smaller model:
ollama pull llama3.2:3b
# Then use: config={'model': 'llama3.2:3b'}
```

## Recommended Models

| Your RAM | Use This Model | Command |
|----------|----------------|---------|
| 8GB | llama3.2:3b | `ollama pull llama3.2:3b` |
| 16GB | llama3.1 | `ollama pull llama3.1` |
| 16GB+ | codellama | `ollama pull codellama` |
| 32GB+ | qwen2.5-coder | `ollama pull qwen2.5-coder` |

## Next Steps

- Read `OLLAMA_SETUP.md` for detailed configuration
- Try different models to see which works best
- Build a Streamlit dashboard (see `QUICKSTART.md`)

## Need Help?

- Full guide: `OLLAMA_SETUP.md`
- Ollama docs: https://ollama.com
- Vanna docs: https://vanna.ai/docs/

---

**Enjoy free local AI! 🚀**

