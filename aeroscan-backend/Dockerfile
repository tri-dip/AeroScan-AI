# syntax=docker/dockerfile:1

# --- Builder ---------------------------------------------------------------
# Installs the uv-managed dependency set (including opencv-python-headless /
# onnxruntime, which need real wheels, hence build-essential as a fallback in
# case no prebuilt wheel matches the target platform) and pre-downloads the
# ArcFace/SCRFD face model pack so the runtime image never needs to reach
# GitHub on its first request.
FROM python:3.14-slim-bookworm AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender1 \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    FACE_MODEL_CACHE_DIR=/opt/aeroscan-models

# Install dependencies first (separate layer from source so code edits don't
# invalidate the dependency-install cache).
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY app ./app
RUN uv sync --frozen --no-dev

RUN mkdir -p "$FACE_MODEL_CACHE_DIR" \
    && /app/.venv/bin/python -c "from app.services.face_service import _ensure_models_downloaded; _ensure_models_downloaded()"

# --- Runtime -----------------------------------------------------------
FROM python:3.14-slim-bookworm AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender1 \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 appuser

WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    FACE_MODEL_CACHE_DIR=/opt/aeroscan-models

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /opt/aeroscan-models /opt/aeroscan-models
COPY app ./app

RUN chown -R appuser:appuser /app /opt/aeroscan-models
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=3).read()" || exit 1

# ${PORT:-8000} so this also runs unmodified behind platforms that inject a
# PORT env var (e.g. AWS App Runner); ECS/Fargate/EC2 can just map 8000.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
