# ==============================================================================
# Travel Buddy API - Production Dockerfile
# ==============================================================================
# Multi-stage build for optimized image size
# Final image ~150MB vs ~1GB with standard approach

# ------------------------------------------------------------------------------
# Stage 1: Builder - Install dependencies and build wheels
# ------------------------------------------------------------------------------
FROM python:3.13-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels -r requirements.txt

# ------------------------------------------------------------------------------
# Stage 2: Runtime - Minimal production image
# ------------------------------------------------------------------------------
FROM python:3.13-slim as runtime

# Set environment variables
# PYTHONPATH=/app/src is deliberately gone: it made modules importable via two
# paths (`from config` AND `from src.config`), which is why every import in the
# codebase was written twice inside try/except. There is one path now, `src.*`,
# resolved from WORKDIR /app.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Create non-root user for security
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash appuser

# Copy wheels from builder and install
COPY --from=builder /build/wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Copy application code
COPY --chown=appuser:appgroup src/ ./src/
COPY --chown=appuser:appgroup data/ ./data/
COPY --chown=appuser:appgroup scripts/ ./scripts/

# Build the knowledge index into the image.
#
# Two things have to happen here rather than at runtime. Cloud Run's filesystem
# is ephemeral and scales to zero, so an index written at runtime would be
# rebuilt on every cold start. And ChromaDB downloads its ~80MB ONNX embedding
# model on first use -- left to runtime, the first request after a cold start
# would pay for that download. Building here bakes in both.
#
# CHROMA_CACHE points the model somewhere appuser can read after the USER switch.
ENV CHROMA_CACHE=/app/.cache/chroma
RUN mkdir -p /app/.cache && \
    python -m scripts.build_index && \
    chown -R appuser:appgroup /app/data /app/.cache

# Switch to non-root user
USER appuser

# Expose port
EXPOSE ${PORT}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/api/health')" || exit 1

# Run the application
CMD ["sh", "-c", "uvicorn src.api:app --host 0.0.0.0 --port ${PORT}"]
