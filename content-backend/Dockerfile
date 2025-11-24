# Multi-stage Dockerfile for Artify Content Backend
# Optimized for production deployment with minimal image size

# Stage 1: Builder
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies to user directory
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --user -r requirements.txt


# Stage 2: Runtime
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 artify && \
    chown -R artify:artify /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/artify/.local

# Copy application code
COPY --chown=artify:artify . .

# Create necessary directories
RUN mkdir -p logs backups chroma_db && \
    chown -R artify:artify logs backups chroma_db

# Switch to non-root user
USER artify

# Add local Python packages to PATH
ENV PATH=/home/artify/.local/bin:$PATH

# Set Python to run in unbuffered mode
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Health check using curl (more reliable than Python requests)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command (can be overridden)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
