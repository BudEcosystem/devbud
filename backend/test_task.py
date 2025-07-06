#!/usr/bin/env python
"""Test executing a task directly"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv('.env.local')

# Test direct task execution
from app.services.task_queue import execute_task

print("Testing direct task execution...")
try:
    # Execute the task directly (not through Celery)
    result = execute_task(
        "test-task-id",
        "test-repo-id", 
        "/tmp/test-repo",
        "test-branch",
        "test instructions"
    )
    print(f"Task executed: {result}")
except Exception as e:
    print(f"Error executing task: {e}")
    import traceback
    traceback.print_exc()