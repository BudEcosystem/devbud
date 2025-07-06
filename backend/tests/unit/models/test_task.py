import pytest
from datetime import datetime
from uuid import UUID


@pytest.mark.unit
class TestTaskModel:
    """Test Task database model."""
    
    async def test_create_task(self, db):
        """Test creating a new task."""
        from app.models.repository import Repository
        from app.models.task import Task, TaskStatus
        
        # Create repository first
        repo = Repository(
            name="test-repo",
            path="/path/to/test-repo",
            default_branch="main"
        )
        db.add(repo)
        await db.commit()
        await db.refresh(repo)
        
        # Create task
        task = Task(
            repository_id=repo.id,
            branch_name="feature-test",
            instructions="Implement test feature",
            status=TaskStatus.PENDING
        )
        
        db.add(task)
        await db.commit()
        await db.refresh(task)
        
        # Verify
        assert task.id is not None
        assert isinstance(task.id, UUID)
        assert task.repository_id == repo.id
        assert task.branch_name == "feature-test"
        assert task.instructions == "Implement test feature"
        assert task.status == TaskStatus.PENDING
        assert task.worktree_path is None
        assert task.output_log == ""
        assert isinstance(task.created_at, datetime)
        assert task.started_at is None
        assert task.completed_at is None
    
    async def test_task_status_transitions(self, db):
        """Test task status transitions."""
        from app.models.repository import Repository
        from app.models.task import Task, TaskStatus
        
        # Create repository and task
        repo = Repository(name="test-repo", path="/path/to/test-repo")
        db.add(repo)
        await db.commit()
        
        task = Task(
            repository_id=repo.id,
            branch_name="feature-test",
            instructions="Test instructions",
            status=TaskStatus.PENDING
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)
        
        # Start task
        await task.start(db, "/path/to/worktree")
        assert task.status == TaskStatus.RUNNING
        assert task.started_at is not None
        assert task.worktree_path == "/path/to/worktree"
        
        # Complete task
        await task.complete(db, success=True, output="Task completed successfully")
        assert task.status == TaskStatus.COMPLETED
        assert task.completed_at is not None
        assert "Task completed successfully" in task.output_log
        
        # Try to start completed task (should raise error)
        with pytest.raises(ValueError, match="Cannot start task"):
            await task.start(db, "/another/path")
    
    async def test_task_failure(self, db):
        """Test marking task as failed."""
        from app.models.repository import Repository
        from app.models.task import Task, TaskStatus
        
        # Create repository and task
        repo = Repository(name="test-repo", path="/path/to/test-repo")
        db.add(repo)
        await db.commit()
        
        task = Task(
            repository_id=repo.id,
            branch_name="feature-test",
            instructions="Test instructions",
            status=TaskStatus.PENDING
        )
        db.add(task)
        await db.commit()
        
        # Start and fail task
        await task.start(db, "/path/to/worktree")
        await task.complete(db, success=False, output="Error: Task failed")
        
        assert task.status == TaskStatus.FAILED
        assert task.completed_at is not None
        assert "Error: Task failed" in task.output_log
    
    async def test_task_cancellation(self, db):
        """Test cancelling a running task."""
        from app.models.repository import Repository
        from app.models.task import Task, TaskStatus
        
        # Create repository and task
        repo = Repository(name="test-repo", path="/path/to/test-repo")
        db.add(repo)
        await db.commit()
        
        task = Task(
            repository_id=repo.id,
            branch_name="feature-test",
            instructions="Test instructions",
            status=TaskStatus.PENDING
        )
        db.add(task)
        await db.commit()
        
        # Start and cancel task
        await task.start(db, "/path/to/worktree")
        await task.cancel(db, reason="User requested cancellation")
        
        assert task.status == TaskStatus.CANCELLED
        assert task.completed_at is not None
        assert "User requested cancellation" in task.output_log
    
    async def test_append_output(self, db):
        """Test appending output to task log."""
        from app.models.repository import Repository
        from app.models.task import Task, TaskStatus
        
        # Create repository and task
        repo = Repository(name="test-repo", path="/path/to/test-repo")
        db.add(repo)
        await db.commit()
        
        task = Task(
            repository_id=repo.id,
            branch_name="feature-test",
            instructions="Test instructions",
            status=TaskStatus.RUNNING
        )
        db.add(task)
        await db.commit()
        
        # Append output
        await task.append_output(db, "Line 1")
        await task.append_output(db, "Line 2")
        await task.append_output(db, "Line 3")
        
        assert task.output_log == "Line 1\nLine 2\nLine 3\n"
    
    async def test_task_unique_branch_per_repo(self, db):
        """Test that branch names must be unique per repository for active tasks."""
        from app.models.repository import Repository
        from app.models.task import Task, TaskStatus
        from sqlalchemy.exc import IntegrityError
        
        # Create repository
        repo = Repository(name="test-repo", path="/path/to/test-repo")
        db.add(repo)
        await db.commit()
        
        # Create first task
        task1 = Task(
            repository_id=repo.id,
            branch_name="feature-test",
            instructions="First task",
            status=TaskStatus.RUNNING
        )
        db.add(task1)
        await db.commit()
        
        # Try to create second task with same branch name
        task2 = Task(
            repository_id=repo.id,
            branch_name="feature-test",  # Same branch name
            instructions="Second task",
            status=TaskStatus.PENDING
        )
        db.add(task2)
        
        with pytest.raises(IntegrityError):
            await db.commit()