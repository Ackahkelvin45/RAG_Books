# Shepherd Guide: one image for the API (+ built web app) and the worker.
#   docker build -t shepherd .
#   api:    docker run shepherd            (uvicorn, runs migrations first)
#   worker: docker run shepherd worker

# --- 1. web app -----------------------------------------------------------------------
FROM node:22-alpine AS web
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY web/ ./
RUN npm run build

# --- 2. python ------------------------------------------------------------------------
FROM python:3.13-slim-bookworm AS app
COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /usr/local/bin/uv

# curl for the healthcheck; postgresql-client for backups (pg_dump) and restores
RUN apt-get update && apt-get install -y --no-install-recommends curl postgresql-client \
 && rm -rf /var/lib/apt/lists/*

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/opt/venv \
    PYTHONUNBUFFERED=1 PYTHONPATH=/app:/app/shared \
    HF_HOME=/models HF_HUB_DISABLE_XET=1 \
    PATH=/opt/venv/bin:$PATH
WORKDIR /app

# dependencies first, so code changes don't re-download torch
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

COPY api ./api
COPY db ./db
COPY shared ./shared
COPY worker ./worker
COPY eval ./eval
COPY --from=web /web/dist ./web/dist
COPY infra/entrypoint.sh /entrypoint.sh

RUN useradd --create-home --uid 1000 shepherd \
 && mkdir -p /models && chown -R shepherd:shepherd /models /app \
 && chmod +x /entrypoint.sh
USER shepherd

EXPOSE 8010
HEALTHCHECK --interval=30s --timeout=5s --start-period=120s --retries=3 \
  CMD curl -fsS http://localhost:8010/api/auth/config || exit 1

ENTRYPOINT ["/entrypoint.sh"]
CMD ["api"]
