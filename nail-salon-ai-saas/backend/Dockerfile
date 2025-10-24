# Multi-stage build for optimized production image
# Stage 1: Build stage with conda
FROM continuumio/miniconda3:latest AS builder

WORKDIR /app

# Copy environment files
COPY environment.yml requirements.txt ./

# Create conda environment
RUN conda env create -f environment.yml && \
    conda clean -afy

# Stage 2: Runtime stage
FROM continuumio/miniconda3:latest

WORKDIR /app

# Install system dependencies including bcrypt requirements
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    build-essential \
    python3-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy conda environment from builder
COPY --from=builder /opt/conda/envs/nail-salon-ai /opt/conda/envs/nail-salon-ai

# Set PATH to use conda environment
ENV PATH=/opt/conda/envs/nail-salon-ai/bin:$PATH
ENV CONDA_DEFAULT_ENV=nail-salon-ai
ENV CONDA_PREFIX=/opt/conda/envs/nail-salon-ai

# Copy application code
COPY . .

# Create directories for data persistence
RUN mkdir -p /app/tenant_data /app/logs /app/training

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)"

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]