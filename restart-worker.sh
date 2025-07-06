#!/bin/bash
# Script to restart the Celery worker

echo "Stopping any existing Celery workers..."
pkill -f "celery.*worker" || true

sleep 2

echo "Starting Celery worker..."
cd /home/budadmin/devbud/backend
export $(cat .env.local | xargs)
PYTHONPATH=. venv/bin/python -m celery -A app.services.task_queue worker --loglevel=info --pool=solo