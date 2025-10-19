# =========================================================
# Stage 1: Frontend Build (React + Vite + TypeScript)
# =========================================================
FROM node:20-bookworm AS frontend-builder

WORKDIR /app

# Copy dependency files first for caching
COPY package*.json ./
COPY tsconfig*.json ./
COPY vite.config.* ./
COPY tailwind.config.* ./
COPY postcss.config.* ./
COPY eslint.config.* ./

# Install all dependencies (include devDependencies)
RUN npm ci

# Copy application source
COPY src/ ./src/
COPY public/ ./public/
COPY index.html ./

# Build the production frontend
RUN npm run build

# =========================================================
# Stage 2: Python Backend (Flask)
# =========================================================
FROM python:3.11-slim AS backend

WORKDIR /app

# Install minimal system dependencies (for pip builds, curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies
COPY python/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY python/ ./

# Copy built frontend from previous stage
COPY --from=frontend-builder /app/dist ./static

# Create necessary directories
RUN mkdir -p /app/temp /app/data

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

# Expose Flask port
EXPOSE 5001

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5001/api/health || exit 1

# Start Flask app
CMD ["python", "app.py"]
