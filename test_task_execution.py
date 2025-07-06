#!/usr/bin/env python3
"""Test script to verify task execution is working properly."""
import requests
import json
import time

API_URL = "http://localhost:8000/api/v1"

def test_task_execution():
    # First, create a test repository
    print("Creating test repository...")
    repo_data = {
        "name": "test-repo",
        "path": "/tmp/test-repo"
    }
    
    # Create a test git repo
    import subprocess
    subprocess.run(["mkdir", "-p", "/tmp/test-repo"], check=True)
    subprocess.run(["git", "init"], cwd="/tmp/test-repo", check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd="/tmp/test-repo", check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd="/tmp/test-repo", check=True)
    subprocess.run(["touch", "README.md"], cwd="/tmp/test-repo", check=True)
    subprocess.run(["git", "add", "."], cwd="/tmp/test-repo", check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd="/tmp/test-repo", check=True)
    
    # Create repository in API
    resp = requests.post(f"{API_URL}/repositories", json=repo_data)
    if resp.status_code != 201:
        print(f"Failed to create repository: {resp.text}")
        return
    
    repo = resp.json()
    print(f"Created repository: {repo['id']}")
    
    # Create a task
    print("\nCreating test task...")
    task_data = {
        "repository_id": repo['id'],
        "branch_name": "test-task",
        "instructions": "Create a simple hello.txt file with 'Hello from Claude' content"
    }
    
    resp = requests.post(f"{API_URL}/tasks", json=task_data)
    if resp.status_code != 201:
        print(f"Failed to create task: {resp.text}")
        return
    
    task = resp.json()
    print(f"Created task: {task['id']} with status: {task['status']}")
    
    # Poll task status
    print("\nMonitoring task status...")
    for i in range(30):  # Poll for up to 30 seconds
        time.sleep(1)
        resp = requests.get(f"{API_URL}/tasks/{task['id']}")
        if resp.status_code == 200:
            task = resp.json()
            print(f"  {i+1}s: Status = {task['status']}")
            if task['status'] not in ['pending', 'running']:
                break
    
    # Get final task output
    print("\nFinal task status:")
    resp = requests.get(f"{API_URL}/tasks/{task['id']}/output")
    if resp.status_code == 200:
        output = resp.json()
        print(f"Task output:\n{output['output']}")
    
    # Cleanup
    subprocess.run(["rm", "-rf", "/tmp/test-repo"], check=True)
    
    return task['status']

if __name__ == "__main__":
    status = test_task_execution()
    print(f"\nTest completed. Final status: {status}")
    if status == 'pending':
        print("ERROR: Task remained in pending state!")
    elif status == 'failed':
        print("Task failed - check output for details")
    elif status == 'completed':
        print("SUCCESS: Task completed successfully!")