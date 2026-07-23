#!/bin/bash
# ─────────────────────────────────────────────────────
# Ready2Go CRM — Production Startup Script
# ─────────────────────────────────────────────────────
# This script runs before the application starts.
# It applies pending database migrations, then launches
# the FastAPI server via uvicorn.
#
# Render will execute this as the start command.
# ─────────────────────────────────────────────────────

echo "=== Ready2Go CRM Startup ==="
echo "Environment: ${ENVIRONMENT:-development}"
echo ""

# Run database migrations
echo "--- Applying database migrations ---"
alembic upgrade head
MIGRATION_EXIT=$?
if [ $MIGRATION_EXIT -ne 0 ]; then
  echo "WARNING: Migration exit code ${MIGRATION_EXIT}. The app will still start,"
  echo "         but the /ready endpoint will report 'degraded' until"
  echo "         all migrations are applied."
fi
echo "Migrations complete."
echo ""

# Start the application server
echo "--- Starting application server ---"
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 4 --proxy-headers --forwarded-allow-ips "*"
