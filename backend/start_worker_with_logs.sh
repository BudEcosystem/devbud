#!/bin/bash
# Start worker with logs saved to file

export $(cat .env.local | xargs)

# Create logs directory
mkdir -p logs

# Start worker with logs
echo "Starting Celery worker with logs..."
echo "Logs will be saved to: logs/celery_worker.log"

PYTHONPATH=. venv/bin/celery -A app.services.task_queue worker \
    --loglevel=DEBUG \
    --logfile=logs/celery_worker.log \
    --pool=solo \
    --hostname=worker@claude-test \
    2>&1 | tee logs/celery_worker_console.log