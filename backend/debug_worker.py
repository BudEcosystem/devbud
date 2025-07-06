#!/usr/bin/env python
"""Debug script to test Celery worker connection"""
import os
import sys

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
from dotenv import load_dotenv
load_dotenv('.env.local')

print("Environment variables:")
print(f"REDIS_URL: {os.getenv('REDIS_URL')}")
print(f"DATABASE_URL: {os.getenv('DATABASE_URL')}")
print(f"WORKTREE_BASE_PATH: {os.getenv('WORKTREE_BASE_PATH')}")
print()

try:
    from app.services.task_queue import celery_app, execute_task
    print("Successfully imported Celery app")
    print(f"Broker URL: {celery_app.conf.broker_url}")
    print(f"Registered tasks: {list(celery_app.tasks.keys())}")
    print()
    
    # Try to connect to Redis
    from redis import Redis
    redis_client = Redis.from_url(os.getenv('REDIS_URL'))
    redis_client.ping()
    print("✅ Redis connection successful")
    
    # Check queue length
    queue_length = redis_client.llen('celery')
    print(f"Tasks in queue: {queue_length}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()