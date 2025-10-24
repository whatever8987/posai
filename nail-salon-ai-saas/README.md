# 💅 Nail Salon AI - SaaS Platform

**AI-Powered Business Intelligence for Nail Salons**

Transform your nail salon data into actionable insights with natural language queries, automated predictions, and intelligent recommendations.

---

## 🌟 Features

### 🤖 Natural Language SQL Generation
- Ask questions in plain English
- Powered by Vanna AI + Ollama (local LLM)
- Context-aware SQL generation
- Query history and favorites

### 📊 Automated Business Insights
- Real-time anomaly detection
- Inventory alerts
- Revenue trend analysis
- Booking pattern insights

### 🔮 Predictive Analytics
- Revenue forecasting (Prophet)
- Customer churn prediction
- Service demand forecasting
- Customer lifetime value (CLV)

### 💡 Intelligent Recommendations
- Personalized promotions
- Optimal staff scheduling
- Customer retention strategies
- Dynamic pricing suggestions
- Inventory optimization

### 🔗 POS System Integrations
- **API Adapters:** Square, Clover, Lightspeed
- **Database Adapters:** PostgreSQL, MySQL, SQL Server
- **File Adapters:** CSV, Excel
- Automatic data synchronization

### 🏢 Multi-Tenant Architecture
- Complete tenant isolation
- Per-tenant AI training
- Secure data separation
- Scalable design

---

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Clone repository
git clone <your-repo-url>
cd nail-salon-ai-saas

# Create .env file
cat > .env << EOF
POSTGRES_PASSWORD=mysecurepassword123
SECRET_KEY=your-super-secret-jwt-key-at-least-32-chars
GRAFANA_PASSWORD=admin
DEBUG=false
EOF

# Start all services
docker-compose up -d

# Pull LLM model (first time)
docker exec -it nail-salon-ollama ollama pull llama2

# Open browser
open http://localhost
```

**Login:** `admin` / `123456`

### Option 2: Development Mode

See [QUICK_START.md](./QUICK_START.md) for detailed instructions.

---

## 📋 What's Included?

### Backend (FastAPI)
- Multi-tenant REST API
- JWT authentication
- PostgreSQL with schema isolation
- Redis caching
- Celery background tasks
- Vanna AI integration
- Prometheus metrics
- Sentry error tracking

### Frontend (Vue 3 + Vben Admin)
- Modern dashboard UI
- Natural language query interface
- Interactive charts (ECharts)
- Real-time insights feed
- Prediction visualizations
- POS integration wizard

### Infrastructure
- Docker & Docker Compose
- Kubernetes manifests
- Prometheus + Grafana monitoring
- GitHub Actions CI/CD
- Automated security scanning

---

## 📚 Documentation

- **[QUICK_START.md](./QUICK_START.md)** - Get running in 5 minutes
- **[START_HERE.md](./START_HERE.md)** - Architecture & implementation details
- **[DEPLOYMENT.md](./DEPLOYMENT.md)** - Production deployment guide
- **[AI_TRAINING_GUIDE.md](./AI_TRAINING_GUIDE.md)** - Train the AI with your schema

### Phase Completion Reports
- [Phase 7: Deployment & Monitoring](./PHASE7_COMPLETE.md) ✅

---

## 🏗️ Architecture

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │
       v
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│  Frontend   │─────>│   Backend    │─────>│  PostgreSQL │
│   (Vue 3)   │      │  (FastAPI)   │      │ (Multi-tenant)
└─────────────┘      └──────┬───────┘      └─────────────┘
                            │
                ┌───────────┼───────────┐
                v           v           v
          ┌──────────┐ ┌────────┐ ┌────────┐
          │  Vanna   │ │ Redis  │ │ Celery │
          │ + Ollama │ │ Cache  │ │ Workers│
          └──────────┘ └────────┘ └────────┘
```

### Technology Stack

**Backend:**
- FastAPI 0.104 (Python 3.11)
- SQLAlchemy 2.0 (async)
- Vanna AI 0.3.4
- Ollama (local LLM)
- ChromaDB (vector store)
- Celery (background tasks)
- Redis (cache & broker)

**Frontend:**
- Vue 3 + TypeScript
- Vben Admin framework
- ECharts (visualizations)
- TailwindCSS
- Vite

**Infrastructure:**
- Docker & Kubernetes
- Prometheus & Grafana
- Sentry
- GitHub Actions

---

## 🎯 Use Cases

### For Nail Salon Owners
- "Show me revenue by service type this month"
- "Which customers haven't visited in 60 days?"
- "What are my best-selling products?"
- Get automated alerts for low inventory
- Predict revenue for next month
- Identify at-risk customers

### For Managers
- Optimize staff scheduling
- Identify top performers
- Analyze booking patterns
- Track service popularity
- Monitor customer satisfaction

### For Marketing
- Target customers for promotions
- Identify upsell opportunities
- Analyze campaign effectiveness
- Segment customers by behavior

---

## 🔐 Security

- ✅ JWT authentication
- ✅ Multi-tenant data isolation
- ✅ SQL injection prevention
- ✅ Rate limiting
- ✅ CORS configuration
- ✅ SSL/TLS encryption
- ✅ Secret management
- ✅ Automated security scanning

---

## 📊 Monitoring

### Grafana Dashboards
- API request rate & latency
- Database performance
- Cache hit rates
- Celery task queues
- Error rates

### Prometheus Metrics
- HTTP requests (by endpoint, method, status)
- Request duration (p50, p95, p99)
- Custom business metrics

### Sentry Error Tracking
- Automatic error capture
- Performance monitoring
- Release tracking
- User feedback

---

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest tests/ -v --cov=app

# Frontend tests (planned)
cd frontend/apps/web-antd
pnpm test
```

**CI/CD Pipeline:**
- Automated testing on every commit
- Security scanning (Trivy, Safety)
- Code quality checks (Ruff, ESLint)
- Automated deployment to staging

---

## 🚀 Deployment

### Local Development
```bash
docker-compose up -d
```

### Production (Kubernetes)
```bash
kubectl apply -f k8s/
```

See [DEPLOYMENT.md](./DEPLOYMENT.md) for complete guide.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

## 📈 Roadmap

### Phase 1-6: ✅ Complete
- Multi-tenant backend
- POS integrations
- Insight engine
- Predictive analytics
- Recommendation engine
- Vue dashboard

### Phase 7: ✅ Complete
- Docker containerization
- Kubernetes manifests
- Monitoring stack
- CI/CD pipeline

### Phase 8: 🚧 Next
- Stripe billing integration
- Admin portal
- Usage tracking
- Feature flags

### Future
- Mobile app (React Native)
- WhatsApp/SMS notifications
- Advanced ML models
- Multi-language support

---

## 📄 License

[Your License Here]

---

## 🙏 Acknowledgments

- **Vanna AI** - SQL generation framework
- **Ollama** - Local LLM runtime
- **Vben Admin** - Vue admin template
- **FastAPI** - Modern Python web framework

---

## 📞 Support

- **Documentation:** See `/docs` folder
- **Issues:** GitHub Issues
- **Email:** support@yourdomain.com

---

## ⭐ Star Us!

If you find this project useful, please give it a star! ⭐

---

**Built with ❤️ for the nail salon industry**

*Transforming data into beautiful insights, one query at a time.*
