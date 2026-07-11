# Stage 1: Builder stage to install and compile Python dependencies
FROM python:3.12-slim AS python-builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Node stage to build the React frontend
FROM node:20-slim AS frontend-builder

WORKDIR /app

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
# Pass environment variables to Vite during build
ENV VITE_API_BASE=/api
ENV VITE_API_KEY=local-dev-key
RUN npm run build

# Stage 3: Final minimal runtime stage serving both backend and frontend
FROM python:3.12-slim AS runner

WORKDIR /app

# Install runtime libpq5 dependency for PostgreSQL client
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy compiled python libraries from python-builder stage
COPY --from=python-builder /root/.local /root/.local

# Copy application backend files
COPY backend ./backend
COPY shared ./shared
COPY config ./config

# Copy frontend static build assets
COPY --from=frontend-builder /app/dist ./frontend/dist

# Ensure the pip user binaries are in PATH
ENV PATH=/root/.local/bin:$PATH
ENV PORT=8000

EXPOSE 8000

CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT}"]
