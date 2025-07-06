import pytest
from unittest.mock import Mock, AsyncMock, patch


@pytest.mark.unit
class TestRepositoryAPI:
    """Test repository API endpoints."""
    
    def test_create_repository(self, client, test_repo_path):
        """Test creating a new repository via API."""
        payload = {
            "name": "test-repo",
            "path": test_repo_path,
            "default_branch": "main",
            "description": "Test repository"
        }
        
        response = client.post("/api/v1/repositories/", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "test-repo"
        assert data["path"] == test_repo_path
        assert data["default_branch"] == "main"
        assert data["description"] == "Test repository"
        assert "id" in data
        assert data["is_active"] is True
    
    def test_create_repository_invalid_path(self, client):
        """Test creating repository with invalid path."""
        payload = {
            "name": "test-repo",
            "path": "/non/existent/path",
            "default_branch": "main"
        }
        
        response = client.post("/api/v1/repositories/", json=payload)
        
        assert response.status_code == 400
        assert "does not exist" in response.json()["detail"]
    
    def test_create_repository_not_git_repo(self, client, tmp_path):
        """Test creating repository with path that's not a git repo."""
        # Create a directory that's not a git repo
        non_git_path = tmp_path / "not-a-repo"
        non_git_path.mkdir()
        
        payload = {
            "name": "test-repo",
            "path": str(non_git_path),
            "default_branch": "main"
        }
        
        response = client.post("/api/v1/repositories/", json=payload)
        
        assert response.status_code == 400
        assert "not a git repository" in response.json()["detail"]
    
    def test_list_repositories(self, client):
        """Test listing all repositories."""
        # First create some repositories
        for i in range(3):
            payload = {
                "name": f"repo-{i}",
                "path": f"/path/to/repo-{i}",
                "default_branch": "main"
            }
            with patch('app.api.endpoints.repositories.validate_git_repository', return_value=True):
                client.post("/api/v1/repositories/", json=payload)
        
        response = client.get("/api/v1/repositories/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all("id" in repo for repo in data)
        assert all("name" in repo for repo in data)
    
    def test_get_repository_by_id(self, client, test_repo_path):
        """Test getting a specific repository by ID."""
        # Create repository
        payload = {
            "name": "test-repo",
            "path": test_repo_path,
            "default_branch": "main"
        }
        create_response = client.post("/api/v1/repositories/", json=payload)
        repo_id = create_response.json()["id"]
        
        # Get repository
        response = client.get(f"/api/v1/repositories/{repo_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == repo_id
        assert data["name"] == "test-repo"
        assert data["path"] == test_repo_path
    
    def test_get_repository_not_found(self, client):
        """Test getting non-existent repository."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/v1/repositories/{fake_id}")
        
        assert response.status_code == 404
        assert "Repository not found" in response.json()["detail"]
    
    def test_update_repository(self, client, test_repo_path):
        """Test updating repository details."""
        # Create repository
        payload = {
            "name": "test-repo",
            "path": test_repo_path,
            "default_branch": "main"
        }
        create_response = client.post("/api/v1/repositories/", json=payload)
        repo_id = create_response.json()["id"]
        
        # Update repository
        update_payload = {
            "description": "Updated description",
            "default_branch": "develop"
        }
        response = client.patch(f"/api/v1/repositories/{repo_id}", json=update_payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated description"
        assert data["default_branch"] == "develop"
        assert data["name"] == "test-repo"  # Unchanged
    
    def test_delete_repository(self, client, test_repo_path):
        """Test soft deleting a repository."""
        # Create repository
        payload = {
            "name": "test-repo",
            "path": test_repo_path,
            "default_branch": "main"
        }
        create_response = client.post("/api/v1/repositories/", json=payload)
        repo_id = create_response.json()["id"]
        
        # Delete repository
        response = client.delete(f"/api/v1/repositories/{repo_id}")
        
        assert response.status_code == 204
        
        # Verify it's soft deleted (still exists but inactive)
        get_response = client.get(f"/api/v1/repositories/{repo_id}")
        assert get_response.status_code == 200
        assert get_response.json()["is_active"] is False
    
    def test_get_repository_tasks(self, client, test_repo_path):
        """Test getting tasks for a repository."""
        # Create repository
        payload = {
            "name": "test-repo",
            "path": test_repo_path,
            "default_branch": "main"
        }
        create_response = client.post("/api/v1/repositories/", json=payload)
        repo_id = create_response.json()["id"]
        
        # Mock tasks
        with patch('app.api.endpoints.repositories.get_repository_tasks') as mock_get_tasks:
            mock_get_tasks.return_value = [
                {"id": "task-1", "branch_name": "feature-1", "status": "pending"},
                {"id": "task-2", "branch_name": "feature-2", "status": "running"}
            ]
            
            response = client.get(f"/api/v1/repositories/{repo_id}/tasks")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["branch_name"] == "feature-1"
        assert data[1]["branch_name"] == "feature-2"