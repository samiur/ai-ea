# Production image for the AI Executive Assistant API.
# Multi-stage: uv binary sourced from the official pinned image.
FROM ghcr.io/astral-sh/uv:0.8.17 AS uv

FROM python:3.12-slim AS base

# Pull patched OS packages the base image hasn't rebuilt with yet
# (keeps the Trivy HIGH/CRITICAL gate green between base-image releases)
RUN apt-get update \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*

COPY --from=uv /uv /uvx /usr/local/bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Dependency files first so the install layer caches across source changes
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

COPY src/ ./src/
# (alembic/ + alembic.ini arrive in Step 14 — add those COPY lines then)

EXPOSE 8000

CMD ["uv", "run", "--no-sync", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
