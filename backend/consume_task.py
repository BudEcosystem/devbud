#!/usr/bin/env python
"""Manually consume a task from the queue"""
import os
import sys
import json
import base64

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv('.env.local')

from redis import Redis

redis_client = Redis.from_url(os.getenv('REDIS_URL'))

# Get task from queue
task_data = redis_client.lpop('celery')
if task_data:
    task = json.loads(task_data)
    print("Task found in queue:")
    print(json.dumps(task, indent=2))
    
    # Decode the body
    body = json.loads(base64.b64decode(task['body']))
    print("\nTask arguments:")
    print(f"  Task ID: {body[0][0]}")
    print(f"  Repository ID: {body[0][1]}")
    print(f"  Repo Path: {body[0][2]}")
    print(f"  Branch: {body[0][3]}")
    print(f"  Instructions: {body[0][4]}")
    
    # Put it back in the queue
    redis_client.lpush('celery', task_data)
    print("\nTask returned to queue")
else:
    print("No tasks in queue")