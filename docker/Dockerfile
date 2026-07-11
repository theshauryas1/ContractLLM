# Stage 1: Builder stage to install and compile dependencies
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Final minimal runtime stage
FROM python:3.12-slim AS runner

WORKDIR /app

# Install runtime libpq5 dependency for PostgreSQL client
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy compiled python libraries from builder stage
COPY --from=builder /root/.local /root/.local
COPY backend ./backend
COPY shared ./shared
COPY config ./config

# Ensure the pip user binaries are in PATH
ENV PATH=/root/.local/bin:$PATH
ENV PORT=8000

EXPOSE 8000

CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT}"]
