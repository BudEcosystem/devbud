from celery import Celery
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from uuid import UUID
import os
from datetime import datetime

from app.core.config import settings
from app.models import Task, Repository, TaskStatus
from app.services.git_manager import GitWorktreeManager
from app.services.claude_runner import ClaudeCodeRunner
from app.services.websocket_manager import broadcast_task_output
import asyncio

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

# Create synchronous database engine
SYNC_DATABASE_URL = settings.DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')
sync_engine = create_engine(SYNC_DATABASE_URL)
SyncSessionLocal = sessionmaker(bind=sync_engine)


def run_async(coro):
    """Run async coroutine in sync context."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name='execute_task')
def execute_task(
    task_id: str,
    repository_id: str,
    repo_path: str,
    branch_name: str,
    instructions: str
):
    """Execute a Claude Code task in the background."""
    git_manager = GitWorktreeManager(base_path=settings.WORKTREE_BASE_PATH)
    claude_runner = ClaudeCodeRunner()
    
    with SyncSessionLocal() as db:
        # Get task from database
        task = db.query(Task).filter(Task.id == UUID(task_id)).first()
        
        if not task:
            return
        
        try:
            # Create worktree
            try:
                worktree_path = run_async(git_manager.create_worktree(
                    repo_path=repo_path,
                    branch_name=branch_name
                ))
            except Exception as e:
                error_msg = f"Failed to create worktree: {str(e)}"
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.utcnow()
                task.output = (task.output or "") + f"\n{error_msg}\nTask failed at {task.completed_at}\n"
                db.commit()
                run_async(broadcast_task_output(task_id, error_msg))
                raise e
            
            # Start task
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.utcnow()
            task.worktree_path = worktree_path
            task.output = f"Task started at {task.started_at}\n"
            db.commit()
            
            run_async(broadcast_task_output(task_id, f"Task started at {task.started_at}\n"))
            
            # Stream output from Claude Code
            output_buffer = []
            
            async def process_claude_output():
                async for output in claude_runner.start_task(task_id, worktree_path, instructions):
                    output_buffer.append(output)
                    task.output = (task.output or "") + output
                    db.commit()
                    await broadcast_task_output(task_id, output)
            
            run_async(process_claude_output())
            
            # Task completed
            success = run_async(claude_runner.get_task_status(task_id)) == "completed"
            
            task.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
            task.completed_at = datetime.utcnow()
            task.output = (task.output or "") + f"\nTask completed at {task.completed_at}\n"
            db.commit()
            
        except Exception as e:
            # Task failed
            error_msg = f"Task failed: {str(e)}"
            if task.status != TaskStatus.FAILED:
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.utcnow()
                task.output = (task.output or "") + f"\n{error_msg}\n"
                task.error_message = str(e)
                db.commit()
            
            # Broadcast error
            run_async(broadcast_task_output(task_id, error_msg))
            
            raise e