import pytest
from datetime import datetime
from uuid import UUID


@pytest.mark.unit
class TestRepositoryModel:
    """Test Repository database model."""
    
    async def test_create_repository(self, db):
        """Test creating a new repository."""
        from app.models.repository import Repository
        
        # Create repository
        repo = Repository(
            name="test-repo",
            path="/path/to/test-repo",
            default_branch="main",
            description="Test repository"
        )
        
        db.add(repo)
        await db.commit()
        await db.refresh(repo)
        
        # Verify
        assert repo.id is not None
        assert isinstance(repo.id, UUID)
        assert repo.name == "test-repo"
        assert repo.path == "/path/to/test-repo"
        assert repo.default_branch == "main"
        assert repo.description == "Test repository"
        assert repo.is_active is True
        assert isinstance(repo.created_at, datetime)
        assert isinstance(repo.updated_at, datetime)
    
    async def test_repository_unique_path(self, db):
        """Test that repository paths must be unique."""
        from app.models.repository import Repository
        from sqlalchemy.exc import IntegrityError
        
        # Create first repository
        repo1 = Repository(
            name="repo1",
            path="/path/to/repo",
            default_branch="main"
        )
        db.add(repo1)
        await db.commit()
        
        # Try to create second repository with same path
        repo2 = Repository(
            name="repo2",
            path="/path/to/repo",  # Same path
            default_branch="main"
        )
        db.add(repo2)
        
        with pytest.raises(IntegrityError):
            await db.commit()
    
    async def test_repository_relationships(self, db):
        """Test repository relationships with tasks."""
        from app.models.repository import Repository
        from app.models.task import Task, TaskStatus
        
        # Create repository
        repo = Repository(
            name="test-repo",
            path="/path/to/test-repo",
            default_branch="main"
        )
        db.add(repo)
        await db.commit()
        await db.refresh(repo)
        
        # Create tasks
        task1 = Task(
            repository_id=repo.id,
            branch_name="feature-1",
            instructions="Implement feature 1",
            status=TaskStatus.PENDING
        )
        task2 = Task(
            repository_id=repo.id,
            branch_name="feature-2",
            instructions="Implement feature 2",
            status=TaskStatus.COMPLETED
        )
        
        db.add_all([task1, task2])
        await db.commit()
        
        # Refresh and check relationships
        await db.refresh(repo)
        tasks = await repo.get_tasks(db)
        
        assert len(tasks) == 2
        assert tasks[0].repository_id == repo.id
        assert tasks[1].repository_id == repo.id
    
    async def test_soft_delete_repository(self, db):
        """Test soft deleting a repository."""
        from app.models.repository import Repository
        
        # Create repository
        repo = Repository(
            name="test-repo",
            path="/path/to/test-repo",
            default_branch="main"
        )
        db.add(repo)
        await db.commit()
        await db.refresh(repo)
        
        # Soft delete
        await repo.soft_delete(db)
        
        assert repo.is_active is False
        assert repo.deleted_at is not None
        assert isinstance(repo.deleted_at, datetime)