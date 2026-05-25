#!/bin/bash
set -e
PORT=${PORT:-8000}
echo "Running database migrations..."
alembic upgrade head
echo "Migrations complete. Starting server..."
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
