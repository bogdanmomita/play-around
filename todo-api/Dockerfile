# --- Stage 1: Builder ---
# We use a multi-stage build. The first stage installs all dependencies.
# The second stage copies only what's needed to run — no build tools, no cache.
# This keeps the final image small and reduces the attack surface.
FROM python:3.12-slim AS builder

WORKDIR /app

# Copy requirements first — before the app code.
# Docker caches each layer. If requirements.txt hasn't changed,
# Docker reuses the cached pip install layer even if app code changed.
# This makes rebuilds much faster during development.
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# --- Stage 2: Runtime ---
FROM python:3.12-slim

WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /install /usr/local

# Copy application code
COPY app/ ./app/

# Run as a non-root user — security best practice.
# If someone exploits the app, they get a low-privilege user, not root.
RUN useradd --no-create-home appuser
USER appuser

# Document that the container listens on port 8000.
# This doesn't actually expose the port — docker run -p does that.
EXPOSE 8000

# uvicorn is the ASGI server that runs FastAPI.
# --host 0.0.0.0 means listen on all network interfaces (required in containers).
# --workers 2 means 2 worker processes to handle concurrent requests.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
