#!/usr/bin/env bash
# ABOUTME: Destroys and recreates the local PostgreSQL database (ALL DATA LOST).
set -euo pipefail
cd "$(dirname "$0")/.."

echo "WARNING: this deletes the local database volume and ALL its data."
read -r -p "Type 'reset' to continue: " answer
if [ "$answer" != "reset" ]; then
  echo "Aborted."
  exit 1
fi

docker compose down --volumes postgres 2>/dev/null || docker compose down --volumes
docker compose up -d postgres
echo "Database reset. Fresh postgres starting on localhost:5432."
