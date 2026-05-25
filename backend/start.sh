#!/bin/bash
set -e
PORT=${PORT:-8000}
echo "Running database migrations..."
alembic upgrade head
echo "Migrations complete."
echo "Starting ARQ worker..."
arq app.workers.worker_config.WorkerSettings &
echo "Starting web server..."
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
