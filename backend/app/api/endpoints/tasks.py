from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.models import Task, Repository, TaskStatus
from app.schemas.task import (
    Task as TaskSchema,
    TaskCreate,
    TaskOutput
)
from app.services.task_queue import execute_task

router = APIRouter()


@router.post("/", response_model=TaskSchema, status_code=status.HTTP_201_CREATED)
async def create_task(
    task: TaskCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new task."""
    # Verify repository exists
    repo_query = select(Repository).where(Repository.id == task.repository_id)
    repo_result = await db.execute(repo_query)
    repository = repo_result.scalar_one_or_none()
    
    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )
    
    # Check if branch already has an active task
    existing_query = select(Task).where(
        and_(
            Task.repository_id == task.repository_id,
            Task.branch_name == task.branch_name,
            Task.status.in_([TaskStatus.PENDING, TaskStatus.RUNNING])
        )
    )
    existing_result = await db.execute(existing_query)
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Branch '{task.branch_name}' already has an active task"
        )
    
    # Create task
    db_task = Task(**task.dict())
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    
    # Load the relationship
    query = select(Task).options(selectinload(Task.repository)).where(Task.id == db_task.id)
    result = await db.execute(query)
    db_task = result.scalar_one()
    
    # Queue task for execution
    execute_task.delay(
        str(db_task.id),
        str(repository.id),
        repository.path,
        db_task.branch_name,
        db_task.instructions
    )
    
    return db_task


@router.get("/", response_model=List[TaskSchema])
async def list_tasks(
    repository_id: Optional[UUID] = Query(None),
    status: Optional[TaskStatus] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List all tasks with optional filters."""
    query = select(Task).options(selectinload(Task.repository))
    
    if repository_id:
        query = query.where(Task.repository_id == repository_id)
    
    if status:
        query = query.where(Task.status == status)
    
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    return tasks


@router.get("/{task_id}", response_model=TaskSchema)
async def get_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific task by ID."""
    query = select(Task).options(selectinload(Task.repository)).where(Task.id == task_id)
    result = await db.execute(query)
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    return task


@router.post("/{task_id}/cancel")
async def cancel_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Cancel a running task."""
    query = select(Task).where(Task.id == task_id)
    result = await db.execute(query)
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    if task.status not in [TaskStatus.PENDING, TaskStatus.RUNNING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel task in {task.status} status"
        )
    
    # Cancel the task
    await task.cancel(db, reason="User requested cancellation")
    
    # TODO: Stop the actual Claude process if running
    
    return {"message": "Task cancelled successfully"}


@router.get("/{task_id}/output", response_model=TaskOutput)
async def get_task_output(
    task_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get the output log for a task."""
    query = select(Task).where(Task.id == task_id)
    result = await db.execute(query)
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    return TaskOutput(
        task_id=task.id,
        output=task.output
    )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a task."""
    query = select(Task).where(Task.id == task_id)
    result = await db.execute(query)
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    if task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete task in {task.status} status. Cancel it first."
        )
    
    await db.delete(task)
    await db.commit()
    
    return None


# Helper functions for tests
async def get_all_tasks(db: AsyncSession) -> List[dict]:
    """Get all tasks (used in tests)."""
    query = select(Task)
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    return [
        {
            "id": str(task.id),
            "branch_name": task.branch_name,
            "status": task.status.value,
            "repository": {"name": task.repository.name}
        }
        for task in tasks
    ]


async def get_repository_tasks(repo_id: str, db: AsyncSession) -> List[dict]:
    """Get tasks for a specific repository (used in tests)."""
    query = select(Task).where(Task.repository_id == UUID(repo_id))
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    return [
        {
            "id": str(task.id),
            "repository_id": str(task.repository_id),
            "branch_name": task.branch_name,
            "status": task.status.value
        }
        for task in tasks
    ]