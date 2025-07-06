import pytest
from unittest.mock import Mock, AsyncMock, patch
import asyncio


@pytest.mark.unit
class TestTaskAPI:
    """Test task API endpoints."""
    
    def test_create_task(self, client, test_repo_path):
        """Test creating a new task via API."""
        # First create a repository
        repo_payload = {
            "name": "test-repo",
            "path": test_repo_path,
            "default_branch": "main"
        }
        repo_response = client.post("/api/v1/repositories/", json=repo_payload)
        repo_id = repo_response.json()["id"]
        
        # Create task
        task_payload = {
            "repository_id": repo_id,
            "branch_name": "feature-test",
            "instructions": "Implement test feature"
        }
        
        with patch('app.api.endpoints.tasks.execute_task.delay') as mock_celery:
            response = client.post("/api/v1/tasks/", json=task_payload)
        
        assert response.status_code == 201
        data = response.json()
        assert data["repository_id"] == repo_id
        assert data["branch_name"] == "feature-test"
        assert data["instructions"] == "Implement test feature"
        assert data["status"] == "pending"
        assert "id" in data
        mock_celery.assert_called_once()
    
    def test_create_task_invalid_repo(self, client):
        """Test creating task with invalid repository ID."""
        task_payload = {
            "repository_id": "00000000-0000-0000-0000-000000000000",
            "branch_name": "feature-test",
            "instructions": "Test instructions"
        }
        
        response = client.post("/api/v1/tasks/", json=task_payload)
        
        assert response.status_code == 404
        assert "Repository not found" in response.json()["detail"]
    
    def test_create_task_duplicate_branch(self, client, test_repo_path):
        """Test creating task with duplicate branch name."""
        # Create repository
        repo_payload = {
            "name": "test-repo",
            "path": test_repo_path,
            "default_branch": "main"
        }
        repo_response = client.post("/api/v1/repositories/", json=repo_payload)
        repo_id = repo_response.json()["id"]
        
        # Create first task
        task_payload = {
            "repository_id": repo_id,
            "branch_name": "feature-test",
            "instructions": "First task"
        }
        
        with patch('app.api.endpoints.tasks.execute_task.delay'):
            client.post("/api/v1/tasks/", json=task_payload)
        
        # Try to create second task with same branch
        task_payload["instructions"] = "Second task"
        response = client.post("/api/v1/tasks/", json=task_payload)
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    def test_list_tasks(self, client):
        """Test listing all tasks."""
        with patch('app.api.endpoints.tasks.get_all_tasks') as mock_get_tasks:
            mock_get_tasks.return_value = [
                {
                    "id": "task-1",
                    "branch_name": "feature-1",
                    "status": "running",
                    "repository": {"name": "repo-1"}
                },
                {
                    "id": "task-2",
                    "branch_name": "feature-2",
                    "status": "completed",
                    "repository": {"name": "repo-2"}
                }
            ]
            
            response = client.get("/api/v1/tasks/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["status"] == "running"
        assert data[1]["status"] == "completed"
    
    def test_get_task_by_id(self, client, test_repo_path):
        """Test getting a specific task by ID."""
        # Create repository and task
        repo_payload = {
            "name": "test-repo",
            "path": test_repo_path,
            "default_branch": "main"
        }
        repo_response = client.post("/api/v1/repositories/", json=repo_payload)
        repo_id = repo_response.json()["id"]
        
        task_payload = {
            "repository_id": repo_id,
            "branch_name": "feature-test",
            "instructions": "Test instructions"
        }
        
        with patch('app.api.endpoints.tasks.execute_task.delay'):
            create_response = client.post("/api/v1/tasks/", json=task_payload)
        task_id = create_response.json()["id"]
        
        # Get task
        response = client.get(f"/api/v1/tasks/{task_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task_id
        assert data["branch_name"] == "feature-test"
        assert data["instructions"] == "Test instructions"
    
    def test_cancel_task(self, client, test_repo_path):
        """Test cancelling a running task."""
        # Create repository and task
        repo_payload = {
            "name": "test-repo",
            "path": test_repo_path,
            "default_branch": "main"
        }
        repo_response = client.post("/api/v1/repositories/", json=repo_payload)
        repo_id = repo_response.json()["id"]
        
        task_payload = {
            "repository_id": repo_id,
            "branch_name": "feature-test",
            "instructions": "Test instructions"
        }
        
        with patch('app.api.endpoints.tasks.execute_task.delay'):
            create_response = client.post("/api/v1/tasks/", json=task_payload)
        task_id = create_response.json()["id"]
        
        # Cancel task
        with patch('app.api.endpoints.tasks.cancel_task') as mock_cancel:
            mock_cancel.return_value = True
            response = client.post(f"/api/v1/tasks/{task_id}/cancel")
        
        assert response.status_code == 200
        assert response.json()["message"] == "Task cancelled successfully"
        mock_cancel.assert_called_once()
    
    def test_get_task_output(self, client, test_repo_path):
        """Test getting task output/logs."""
        # Create repository and task
        repo_payload = {
            "name": "test-repo",
            "path": test_repo_path,
            "default_branch": "main"
        }
        repo_response = client.post("/api/v1/repositories/", json=repo_payload)
        repo_id = repo_response.json()["id"]
        
        task_payload = {
            "repository_id": repo_id,
            "branch_name": "feature-test",
            "instructions": "Test instructions"
        }
        
        with patch('app.api.endpoints.tasks.execute_task.delay'):
            create_response = client.post("/api/v1/tasks/", json=task_payload)
        task_id = create_response.json()["id"]
        
        # Get task output
        with patch('app.api.endpoints.tasks.get_task_output') as mock_get_output:
            mock_get_output.return_value = "Task output line 1\nTask output line 2\n"
            response = client.get(f"/api/v1/tasks/{task_id}/output")
        
        assert response.status_code == 200
        assert response.json()["output"] == "Task output line 1\nTask output line 2\n"
    
    def test_filter_tasks_by_status(self, client):
        """Test filtering tasks by status."""
        with patch('app.api.endpoints.tasks.get_all_tasks') as mock_get_tasks:
            mock_get_tasks.return_value = [
                {
                    "id": "task-1",
                    "branch_name": "feature-1",
                    "status": "running",
                    "repository": {"name": "repo-1"}
                }
            ]
            
            response = client.get("/api/v1/tasks/?status=running")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "running"
    
    def test_filter_tasks_by_repository(self, client):
        """Test filtering tasks by repository."""
        repo_id = "test-repo-id"
        
        with patch('app.api.endpoints.tasks.get_repository_tasks') as mock_get_tasks:
            mock_get_tasks.return_value = [
                {
                    "id": "task-1",
                    "repository_id": repo_id,
                    "branch_name": "feature-1",
                    "status": "running"
                }
            ]
            
            response = client.get(f"/api/v1/tasks/?repository_id={repo_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["repository_id"] == repo_id