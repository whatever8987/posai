"""
Main FastAPI application
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import time

from .core.config import settings
from .core.database import init_db
from .core.tenancy import TenantMiddleware
from .api.v1 import auth, query, integrations, training, insights, predictions, recommendations, dev_auth, user

# Sentry integration
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
        ],
        traces_sample_rate=0.1,  # 10% of transactions for performance monitoring
        profiles_sample_rate=0.1,  # 10% for profiling
        environment=os.getenv("ENVIRONMENT", "production"),
        release=settings.VERSION,
    )
    print("✓ Sentry error tracking enabled")

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for startup and shutdown events"""
    # Startup
    print("Starting Nail Salon AI SaaS Platform...")
    await init_db()
    print(f"✓ Database initialized")
    print(f"✓ Ollama configured: {settings.OLLAMA_HOST}")
    print(f"✓ Model: {settings.OLLAMA_MODEL}")
    
    yield
    
    # Shutdown
    print("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tenant middleware
app.add_middleware(TenantMiddleware)

# Prometheus metrics middleware
@app.middleware("http")
async def prometheus_middleware(request, call_next):
    """Collect Prometheus metrics for each request"""
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response

# Include routers
# Development auth (simple mock for frontend development)
app.include_router(dev_auth.router, prefix="/api")
# Production routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(user.router, prefix=settings.API_V1_STR)
app.include_router(query.router, prefix=settings.API_V1_STR)
app.include_router(integrations.router, prefix=settings.API_V1_STR)
app.include_router(training.router, prefix=settings.API_V1_STR)
app.include_router(insights.router, prefix=settings.API_V1_STR)
app.include_router(predictions.router, prefix=settings.API_V1_STR)
app.include_router(recommendations.router, prefix=settings.API_V1_STR)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.VERSION,
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Nail Salon AI SaaS Platform API",
        "version": settings.VERSION,
        "docs": "/docs",
    }

