# 🚀 Nail Salon AI - Deployment Guide

Complete guide for deploying Nail Salon AI SaaS Platform.

## Table of Contents
- [Local Development with Docker](#local-development-with-docker)
- [Production Deployment with Kubernetes](#production-deployment-with-kubernetes)
- [Monitoring Setup](#monitoring-setup)
- [CI/CD Pipeline](#cicd-pipeline)
- [Troubleshooting](#troubleshooting)

---

## Local Development with Docker

### Prerequisites
- Docker Desktop installed
- Docker Compose v2.x
- At least 8GB RAM available

### Quick Start

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd nail-salon-ai-saas
```

2. **Create environment file**
```bash
# Create .env file in the root directory
cp .env.example .env

# Edit .env with your values
nano .env
```

Required environment variables:
```env
POSTGRES_PASSWORD=your_secure_password
SECRET_KEY=your-super-secret-jwt-key-min-32-characters
GRAFANA_PASSWORD=admin
DEBUG=false
SENTRY_DSN=  # Optional
```

3. **Start all services**
```bash
docker-compose up -d
```

This will start:
- PostgreSQL (port 5432)
- Redis (port 6379)
- Ollama (port 11434)
- Backend API (port 8000)
- Frontend (port 80)
- Celery Worker
- Celery Beat
- Prometheus (port 9090)
- Grafana (port 3000)

4. **Initialize Ollama model**
```bash
# Pull the LLM model (first time only)
docker exec -it nail-salon-ollama ollama pull llama2
```

5. **Access the application**
- Frontend: http://localhost
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090

### Development Workflow

**View logs:**
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f celery-worker
```

**Restart a service:**
```bash
docker-compose restart backend
```

**Stop all services:**
```bash
docker-compose down
```

**Clean everything (including volumes):**
```bash
docker-compose down -v
```

---

## Production Deployment with Kubernetes

### Prerequisites
- Kubernetes cluster (v1.28+)
- kubectl configured
- Ingress controller (nginx-ingress)
- cert-manager for SSL certificates
- Container registry access (e.g., GitHub Container Registry)

### Step 1: Build and Push Images

**Using GitHub Actions (Recommended):**
```bash
# Simply push to main branch
git push origin main

# Images will be built and pushed to GitHub Container Registry
```

**Manual build:**
```bash
# Build backend
docker build -t ghcr.io/your-org/nail-salon-backend:latest ./backend
docker push ghcr.io/your-org/nail-salon-backend:latest

# Build frontend
docker build -t ghcr.io/your-org/nail-salon-frontend:latest ./frontend
docker push ghcr.io/your-org/nail-salon-frontend:latest
```

### Step 2: Configure Kubernetes

1. **Create namespace**
```bash
kubectl apply -f k8s/namespace.yaml
```

2. **Set up secrets**
```bash
# Create secrets from environment variables
kubectl create secret generic nail-salon-secrets \
  --from-literal=POSTGRES_PASSWORD='your_secure_password' \
  --from-literal=DATABASE_URL='postgresql+asyncpg://nail_salon_user:password@postgres:5432/nail_salon_db' \
  --from-literal=SECRET_KEY='your-jwt-secret-key' \
  --from-literal=REDIS_URL='redis://redis:6379/0' \
  --from-literal=SENTRY_DSN='your-sentry-dsn' \
  --from-literal=GF_SECURITY_ADMIN_PASSWORD='admin' \
  -n nail-salon-ai
```

3. **Update ConfigMap**
```bash
# Edit k8s/configmap.yaml with your domain
kubectl apply -f k8s/configmap.yaml
```

4. **Update image references**
```bash
# Edit k8s/backend-deployment.yaml and k8s/frontend-deployment.yaml
# Replace "your-registry" with your actual registry URL
```

### Step 3: Deploy

```bash
# Apply all manifests in order
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/postgres-statefulset.yaml
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/ingress.yaml
```

### Step 4: Configure Ingress

1. **Install cert-manager (if not installed)**
```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
```

2. **Create ClusterIssuer for Let's Encrypt**
```bash
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

3. **Update ingress with your domain**
```bash
# Edit k8s/ingress.yaml
# Replace "yourdomain.com" with your actual domain
kubectl apply -f k8s/ingress.yaml
```

### Step 5: Verify Deployment

```bash
# Check pods
kubectl get pods -n nail-salon-ai

# Check services
kubectl get services -n nail-salon-ai

# Check ingress
kubectl get ingress -n nail-salon-ai

# View logs
kubectl logs -f deployment/backend -n nail-salon-ai
kubectl logs -f deployment/frontend -n nail-salon-ai
```

### Scaling

**Manual scaling:**
```bash
kubectl scale deployment backend --replicas=5 -n nail-salon-ai
kubectl scale deployment frontend --replicas=3 -n nail-salon-ai
```

**Auto-scaling is configured via HPA:**
- Backend: 3-10 replicas (CPU 70%, Memory 80%)
- Frontend: 2-5 replicas (CPU 70%)

---

## Monitoring Setup

### Prometheus

**Access:** http://prometheus.yourdomain.com (configure ingress)

**Metrics collected:**
- HTTP request rate
- Response time (p50, p95, p99)
- Error rate
- Database connection pool
- Redis operations
- Celery task queue length

### Grafana

**Access:** http://grafana.yourdomain.com

**Default credentials:** admin/admin (change immediately)

**Pre-configured dashboards:**
- Nail Salon AI Overview
- API Performance
- Database Metrics
- Redis Metrics

**Import additional dashboards:**
1. Go to Dashboards → Import
2. Use these IDs:
   - Node Exporter: 1860
   - PostgreSQL: 9628
   - Redis: 11835

### Sentry

**Setup:**
1. Create account at https://sentry.io
2. Create new project for "FastAPI"
3. Copy DSN
4. Add to secrets:
```bash
kubectl create secret generic nail-salon-secrets \
  --from-literal=SENTRY_DSN='your-sentry-dsn' \
  -n nail-salon-ai \
  --dry-run=client -o yaml | kubectl apply -f -
```

**Features:**
- Automatic error tracking
- Performance monitoring
- Release tracking
- User feedback

---

## CI/CD Pipeline

### GitHub Actions

**Workflows included:**
1. **ci-cd.yml** - Main pipeline
   - Run tests (backend + frontend)
   - Build Docker images
   - Push to registry
   - Deploy to Kubernetes

2. **security-scan.yml** - Security checks
   - Dependency scanning
   - Container image scanning
   - Code quality analysis

### Setup

1. **Add GitHub Secrets:**
   - `KUBE_CONFIG`: Base64-encoded kubeconfig file
   - Additional secrets as needed

2. **Enable workflows:**
```bash
# Push to main branch triggers deployment
git push origin main
```

3. **Monitor workflow:**
   - Go to GitHub → Actions tab
   - View workflow runs and logs

### Manual Deployment

If you need to deploy manually:
```bash
# Tag and push
git tag v1.0.0
git push origin v1.0.0

# Or manually trigger workflow from GitHub UI
```

---

## Troubleshooting

### Backend not starting

**Check logs:**
```bash
docker-compose logs backend
# or
kubectl logs -f deployment/backend -n nail-salon-ai
```

**Common issues:**
- Database connection: Verify DATABASE_URL
- Redis connection: Check REDIS_URL
- Ollama not responding: Ensure Ollama service is running

### Frontend 502 errors

**Check:**
1. Backend is healthy: `curl http://localhost:8000/health`
2. Network between frontend and backend
3. Nginx configuration in frontend container

### Database connection pool exhausted

**Solution:**
```bash
# Scale backend replicas
kubectl scale deployment backend --replicas=5 -n nail-salon-ai
```

### Celery tasks not processing

**Check:**
```bash
docker-compose logs celery-worker
# or
kubectl logs -f deployment/celery-worker -n nail-salon-ai
```

**Verify Redis:**
```bash
redis-cli -h localhost -p 6379 ping
```

### SSL certificate issues

**Check cert-manager:**
```bash
kubectl get certificates -n nail-salon-ai
kubectl describe certificate nail-salon-tls -n nail-salon-ai
```

**Force renewal:**
```bash
kubectl delete certificate nail-salon-tls -n nail-salon-ai
kubectl apply -f k8s/ingress.yaml
```

### High memory usage

**Check metrics:**
```bash
kubectl top pods -n nail-salon-ai
```

**Solutions:**
- Adjust resource limits in deployment YAML
- Scale horizontally instead of vertically
- Check for memory leaks in application logs

---

## Performance Optimization

### Database

1. **Connection pooling** (already configured in SQLAlchemy)
2. **Indexes** on frequently queried columns
3. **Query optimization** - use explain analyze

### Redis

1. **TTL on cached items** (configured)
2. **Eviction policy** - check memory usage
3. **Persistence** - balance between performance and durability

### Backend

1. **Async operations** (already using FastAPI async)
2. **Background tasks** (Celery)
3. **Rate limiting** (consider adding nginx rate limiting)

### Frontend

1. **CDN for static assets**
2. **Browser caching** (configured in nginx)
3. **Code splitting** (Vite handles this)

---

## Backup and Recovery

### Database Backup

**Automated backup:**
```bash
# Create CronJob in Kubernetes
kubectl apply -f k8s/backup-cronjob.yaml
```

**Manual backup:**
```bash
# Docker
docker exec nail-salon-postgres pg_dump -U nail_salon_user nail_salon_db > backup.sql

# Kubernetes
kubectl exec -it postgres-0 -n nail-salon-ai -- pg_dump -U nail_salon_user nail_salon_db > backup.sql
```

### Restore

```bash
# Docker
docker exec -i nail-salon-postgres psql -U nail_salon_user nail_salon_db < backup.sql

# Kubernetes
kubectl exec -i postgres-0 -n nail-salon-ai -- psql -U nail_salon_user nail_salon_db < backup.sql
```

---

## Security Checklist

- [ ] Change all default passwords
- [ ] Use strong SECRET_KEY (32+ characters)
- [ ] Enable HTTPS/TLS
- [ ] Configure CORS properly
- [ ] Set up firewall rules
- [ ] Enable Sentry for error tracking
- [ ] Regular security scans (GitHub Actions)
- [ ] Backup database regularly
- [ ] Implement rate limiting
- [ ] Keep dependencies updated

---

## Support

For issues or questions:
- GitHub Issues: [your-repo-url]/issues
- Documentation: [your-docs-url]
- Email: support@yourdomain.com

---

**Last updated:** 2025-10-24
**Version:** 1.0.0

