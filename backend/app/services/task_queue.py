from celery import Celery
from celery.result import AsyncResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models import Task, Repository, TaskStatus
from app.services.git_manager import GitWorktreeManager
from app.services.claude_runner import ClaudeCodeRunner
from app.services.websocket_manager import broadcast_task_output

# Create Celery app
celery_app = Celery('devbud', broker=settings.REDIS_URL)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)


@asynccontextmanager
async def get_db_session():
    """Get database session for Celery tasks."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@celery_app.task(name='execute_task')
def execute_task(
    task_id: str,
    repository_id: str,
    repo_path: str,
    branch_name: str,
    instructions: str
):
    """Execute a Claude Code task in the background."""
    # Run async function in sync context
    asyncio.run(_execute_task_async(
        task_id,
        repository_id,
        repo_path,
        branch_name,
        instructions
    ))


async def _execute_task_async(
    task_id: str,
    repository_id: str,
    repo_path: str,
    branch_name: str,
    instructions: str
):
    """Async implementation of task execution."""
    git_manager = GitWorktreeManager(base_path=settings.WORKTREE_BASE_PATH)
    claude_runner = ClaudeCodeRunner()
    
    async with get_db_session() as db:
        # Get task from database
        query = select(Task).where(Task.id == UUID(task_id))
        result = await db.execute(query)
        task = result.scalar_one_or_none()
        
        if not task:
            return
        
        try:
            # Start the task
            try:
                worktree_path = await git_manager.create_worktree(
                    repo_path=repo_path,
                    branch_name=branch_name
                )
            except Exception as e:
                error_msg = f"Failed to create worktree: {str(e)}"
                await task.append_output(db, error_msg)
                # Ensure task is marked as failed since it never started
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.utcnow()
                task.output = (task.output or "") + f"\nTask failed at {task.completed_at}\n"
                db.add(task)
                await db.commit()
                await broadcast_task_output(task_id, error_msg)
                raise e
            
            await task.start(db, worktree_path)
            
            # Stream output from Claude Code
            output_buffer = []
            async for output in claude_runner.start_task(task_id, worktree_path, instructions):
                # Save output
                output_buffer.append(output)
                await task.append_output(db, output)
                
                # Broadcast to WebSocket clients
                await broadcast_task_output(task_id, output)
            
            # Task completed
            success = await claude_runner.get_task_status(task_id) == "completed"
            await task.complete(db, success=success)
            
        except Exception as e:
            # Task failed
            error_msg = f"Task failed: {str(e)}"
            if task.status != TaskStatus.FAILED:
                await task.append_output(db, error_msg)
                await task.complete(db, success=False, output=error_msg)
            
            # Broadcast error
            await broadcast_task_output(task_id, error_msg)
            
            raise e


def get_task_result(task_id: str) -> AsyncResult:
    """Get the result of a Celery task."""
    return AsyncResult(task_id, app=celery_app)