# GreenOps Refactor — Dockerfile
# Multi-stage production-ready build optimized for Docker Hub

# ═══════════════════════════════════════════════════════
# STAGE 1: Builder - Install dependencies
# ═══════════════════════════════════════════════════════
FROM python:3.11-slim AS builder

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR /tmp

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools && \
    pip install --no-cache-dir -r requirements.txt

# ═══════════════════════════════════════════════════════
# STAGE 2: Runtime - Lean production image
# ═══════════════════════════════════════════════════════
FROM python:3.11-slim

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Set working directory
WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source code
COPY app.py .
COPY feature_extractor.py .
COPY context_integrator.py .
COPY training_model1.py .
COPY benchmark.py .
COPY requirements.txt .

# Copy templates
COPY templates/ templates/

# Copy pre-trained model files if they exist (optional)
COPY energy_predictor.pkl* ./
COPY feature_columns.json* ./
COPY model_metrics.json* ./

# Create non-root user for security
RUN useradd -m -u 1000 greenops && \
    chown -R greenops:greenops /app

USER greenops

# Set environment variables
ENV FLASK_APP=app.py \
    FLASK_ENV=production \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000

# Expose port
EXPOSE 5000

# Health check - verify app is responding
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Initialize model (if not present) and run app with gunicorn
ENTRYPOINT ["/bin/sh", "-c"]
CMD ["if [ ! -f energy_predictor.pkl ]; then echo 'Training model...'; python training_model1.py; fi && exec gunicorn --bind 0.0.0.0:5000 --workers 4 --worker-class sync --timeout 120 --keep-alive 5 --log-level info --access-logfile - --error-logfile - app:app"]

