#!/usr/bin/env bash
# ABOUTME: Starts the local PostgreSQL container and waits for it to be healthy.
set -euo pipefail
cd "$(dirname "$0")/.."

docker compose up -d postgres

echo "Waiting for postgres to become healthy..."
for _ in $(seq 1 30); do
  status=$(docker inspect --format '{{.State.Health.Status}}' ai-ea-postgres 2>/dev/null || echo "starting")
  if [ "$status" = "healthy" ]; then
    echo "Postgres is ready on localhost:5432."
    exit 0
  fi
  sleep 1
done

echo "Postgres did not become healthy in time." >&2
docker compose logs postgres | tail -20 >&2
exit 1
