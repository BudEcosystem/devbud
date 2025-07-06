#!/usr/bin/env python
"""Diagnose Celery worker issues"""
import os
import sys
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv('.env.local')

print("=== Celery Worker Diagnostics ===\n")

# 1. Check environment
print("1. Environment Variables:")
print(f"   REDIS_URL: {os.getenv('REDIS_URL')}")
print(f"   DATABASE_URL: {os.getenv('DATABASE_URL')[:50]}...")
print(f"   WORKTREE_BASE_PATH: {os.getenv('WORKTREE_BASE_PATH')}")
print()

# 2. Check Redis connection
print("2. Redis Connection:")
try:
    from redis import Redis
    redis_client = Redis.from_url(os.getenv('REDIS_URL'))
    redis_client.ping()
    print("   ✅ Connected to Redis")
    
    # Check queues
    queues = redis_client.keys('*celery*')
    print(f"   Celery queues: {[q.decode() for q in queues]}")
    
    # Check pending tasks
    pending = redis_client.llen('celery')
    print(f"   Pending tasks: {pending}")
except Exception as e:
    print(f"   ❌ Redis error: {e}")
print()

# 3. Check Celery import
print("3. Celery Import:")
try:
    from app.services.task_queue import celery_app, execute_task
    print("   ✅ Celery app imported successfully")
    print(f"   Broker: {celery_app.conf.broker_url}")
    print(f"   Tasks: {list(celery_app.tasks.keys())}")
except Exception as e:
    print(f"   ❌ Import error: {e}")
    import traceback
    traceback.print_exc()
print()

# 4. Check Claude CLI
print("4. Claude Code CLI:")
try:
    result = subprocess.run(['which', 'claude'], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"   ✅ Claude CLI found at: {result.stdout.strip()}")
        
        # Check if logged in
        result = subprocess.run(['claude', 'api', '--help'], capture_output=True, text=True)
        if result.returncode == 0:
            print("   ✅ Claude CLI appears to be authenticated")
        else:
            print("   ⚠️  Claude CLI may not be authenticated")
    else:
        print("   ❌ Claude CLI not found in PATH")
except Exception as e:
    print(f"   ❌ Error checking Claude: {e}")
print()

# 5. Test worker command
print("5. Worker Start Command:")
print("   Run this command to start the worker with verbose logging:")
print("   PYTHONPATH=. venv/bin/celery -A app.services.task_queue worker --loglevel=DEBUG --pool=solo")
print()

# 6. Check for running workers
print("6. Running Workers:")
try:
    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
    celery_processes = [line for line in result.stdout.split('\n') if 'celery' in line and 'worker' in line]
    if celery_processes:
        print("   Found running Celery processes:")
        for proc in celery_processes[:3]:  # Show first 3
            print(f"   - {proc[:100]}...")
    else:
        print("   No Celery worker processes found")
except Exception as e:
    print(f"   Error checking processes: {e}")