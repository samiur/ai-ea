#!/usr/bin/env bash
# ABOUTME: Stops the local PostgreSQL container (data is preserved).
set -euo pipefail
cd "$(dirname "$0")/.."

docker compose stop postgres
echo "Postgres stopped. Data volume preserved; use start-db.sh to resume."
