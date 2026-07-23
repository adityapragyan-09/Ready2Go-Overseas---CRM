# ─────────────────────────────────────────────────────
# Ready2Go CRM — Production Dockerfile
# Multi-stage: Build frontend → Run backend
# ─────────────────────────────────────────────────────

# ── Stage 1: Frontend Build ─────────────────────────
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --ignore-scripts

COPY frontend/ .
RUN npm run build

# ── Stage 2: Backend Runtime ────────────────────────
FROM python:3.11-slim AS backend

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy backend
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY backend/ .

# Copy built frontend from Stage 1
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Create non-root user
RUN useradd --create-home --shell /bin/bash crm && \
    mkdir -p /app/uploads && \
    chown -R crm:crm /app

# Make startup script executable
COPY backend/startup.sh /app/startup.sh
RUN chmod +x /app/startup.sh

USER crm

# Health check uses the PORT env var (Render provides $PORT)
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import os, urllib.request; port = os.environ.get('PORT', '8000'); urllib.request.urlopen(f'http://localhost:{port}/health')" || exit 1

EXPOSE 8000

# Start command runs migrations then starts the server
CMD ["/app/startup.sh"]
