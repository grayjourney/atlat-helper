# -----------------------------------------------------------------------------
# Stage 1: Builder
# -----------------------------------------------------------------------------
# This stage installs all dependencies. We use --user to install to a local
# directory that we can copy to the runtime stage.

FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /app

# Install build dependencies (needed for some Python packages)
# These won't be in the final image!
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first (Docker layer caching optimization)
# If requirements.txt hasn't changed, Docker reuses this layer
COPY requirements.txt .

# Install Python dependencies to user directory
# --user: Install to ~/.local (can copy to runtime stage)
# --no-cache-dir: Don't cache pip packages (smaller image)
RUN pip install --user --no-cache-dir -r requirements.txt

# -----------------------------------------------------------------------------
# Stage 2: Runtime
# -----------------------------------------------------------------------------
# Minimal image with only runtime dependencies

FROM python:3.11-slim AS runtime

# Set working directory
WORKDIR /app

# Install only runtime dependencies (libpq for asyncpg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
# === Why? ===
# If the container is compromised, the attacker has limited permissions
RUN useradd --create-home --shell /bin/bash appuser

# Copy installed packages from builder stage
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Add local bin to PATH (where pip installed packages)
ENV PATH=/home/appuser/.local/bin:$PATH

# Set Python to not buffer output (better for Docker logs)
ENV PYTHONUNBUFFERED=1

# Set environment to production
ENV APP_ENV=production

# Expose the FastAPI port
EXPOSE 8000

# Health check endpoint
# Docker/Kubernetes will use this to verify the container is healthy
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" || exit 1

# Default command: Run FastAPI with Uvicorn
# --host 0.0.0.0: Listen on all interfaces (required in Docker)
# --port 8000: Standard port
# --workers 4: Use multiple workers for production
CMD ["uvicorn", "src.api.server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
