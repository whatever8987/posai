# ⚡ Quick Start Guide

Get Nail Salon AI running in 5 minutes!

## 🐳 Docker Compose (Easiest)

```bash
# 1. Clone and enter directory
git clone <your-repo>
cd nail-salon-ai-saas

# 2. Create .env file
cat > .env << EOF
POSTGRES_PASSWORD=mysecurepassword123
SECRET_KEY=your-super-secret-jwt-key-at-least-32-chars
GRAFANA_PASSWORD=admin
DEBUG=false
EOF

# 3. Start everything
docker-compose up -d

# 4. Pull LLM model (first time only)
docker exec -it nail-salon-ollama ollama pull llama2

# 5. Open browser
open http://localhost
```

**Login credentials:**
- Username: `admin`
- Password: `123456`

---

## 🚀 Development Mode (No Docker)

### Backend

```bash
cd backend

# Create conda environment
conda env create -f environment.yml
conda activate nail-salon-ai

# Set up .env
cp env-example.txt .env
# Edit .env with your values

# Start services (in separate terminals)
# Terminal 1: PostgreSQL
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:16-alpine

# Terminal 2: Redis
docker run -d -p 6379:6379 redis:7-alpine

# Terminal 3: Ollama
docker run -d -p 11434:11434 ollama/ollama:latest
docker exec -it <container-id> ollama pull llama2

# Terminal 4: Backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend/apps/web-antd

# Install dependencies
pnpm install

# Start dev server
pnpm vite --host 127.0.0.1 --port 5173
```

**Access:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/docs

---

## 📊 What's Running?

| Service | Port | URL |
|---------|------|-----|
| Frontend | 80 | http://localhost |
| Backend API | 8000 | http://localhost:8000/docs |
| PostgreSQL | 5432 | - |
| Redis | 6379 | - |
| Ollama | 11434 | http://localhost:11434 |
| Grafana | 3000 | http://localhost:3000 |
| Prometheus | 9090 | http://localhost:9090 |

---

## 🧪 Test the Platform

1. **Login** with admin/123456
2. **Try AI Query:**
   - Go to "AI Query" page
   - Ask: "Show me all customers"
   - The AI will generate SQL!
3. **Check Insights:**
   - View automated business insights
4. **Predictions:**
   - See revenue forecasts and churn risk
5. **Monitoring:**
   - Open Grafana (http://localhost:3000)
   - Login: admin/admin
   - View "Nail Salon AI Overview" dashboard

---

## 🛠️ Common Commands

```bash
# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Restart a service
docker-compose restart backend

# Stop everything
docker-compose down

# Clean everything (including data)
docker-compose down -v
```

---

## 🚨 Troubleshooting

**Backend won't start:**
```bash
# Check if ports are available
lsof -i :8000
lsof -i :5432

# View detailed logs
docker-compose logs backend
```

**Frontend shows 500 errors:**
```bash
# Check backend health
curl http://localhost:8000/health

# Check backend logs
docker-compose logs -f backend
```

**Ollama not responding:**
```bash
# Pull model again
docker exec -it nail-salon-ollama ollama pull llama2

# Check Ollama status
curl http://localhost:11434/api/tags
```

---

## 📚 Next Steps

- Read [DEPLOYMENT.md](./DEPLOYMENT.md) for production deployment
- Check [START_HERE.md](./START_HERE.md) for architecture details
- View [AI_TRAINING_GUIDE.md](./AI_TRAINING_GUIDE.md) to train the AI

---

**Need help?** Open an issue on GitHub!

