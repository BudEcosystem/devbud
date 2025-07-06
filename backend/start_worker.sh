#!/bin/bash
# Start Celery worker with explicit configuration

# Load environment variables
export $(cat .env.local | xargs)

# Start worker with debug logging
echo "Starting Celery worker..."
echo "REDIS_URL: $REDIS_URL"
echo "WORKTREE_BASE_PATH: $WORKTREE_BASE_PATH"

# Run worker with explicit queue name and increased verbosity
venv/bin/python -m celery -A app.services.task_queue worker \
    --loglevel=DEBUG \
    --queues=celery \
    --concurrency=1 \
    --pool=solo