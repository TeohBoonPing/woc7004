#!/usr/bin/env bash
#
# PostgreSQL Idle Stop Script
# Monitors PostgreSQL container for idle connections and stops it when inactive
#
# Usage: ./pg-idle-stop.sh
# Cron: */5 * * * * /path/to/scripts/pg-idle-stop.sh

CONTAINER="postgres"
IDLE_MINUTES=10

# Check for active connections (non-idle states)
ACTIVE=$(docker exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc \
  "SELECT count(*) FROM pg_stat_activity WHERE state NOT IN ('idle');" 2>/dev/null || echo 1)

if [[ "$ACTIVE" -eq 0 ]]; then
  echo "$(date): Postgres idle → stopping container..."
  docker stop postgres
else
  echo "$(date): Postgres has $ACTIVE active connection(s) → keeping container running"
fi
