# ── Stage 1: dependency installer ────────────────────────────────────────
# Using a separate builder stage means dependency layers are cached.
# If requirements.txt doesn't change, Docker reuses the cache layer.
FROM python:3.12-slim AS builder

WORKDIR /build

# Copy only requirements first — this layer is cached until reqs change
COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: runtime image ────────────────────────────────────────────────
# Start fresh from the same slim base — no build tools in final image
FROM python:3.12-slim AS runtime

# Security: create a non-root user to run the application
# Running as root inside a container is a significant security risk
RUN groupadd --gid 1001 appgroup \
    && useradd --uid 1001 --gid appgroup --no-create-home appuser

WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /install /usr/local

# Copy application source (not tests, not .git, not .env — see .dockerignore)
COPY app/ ./app/

# Switch to non-root user before running anything
USER appuser

# Expose the port the app listens on
EXPOSE 8000

# Health check — Docker uses this to determine if the container is healthy
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Runtime command — use uvicorn with production-appropriate settings
# Note: --reload is NOT used in production
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
