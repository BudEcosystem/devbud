from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.models import Repository
from app.schemas.repository import (
    Repository as RepositorySchema,
    RepositoryCreate,
    RepositoryUpdate
)
from app.services.git_manager import GitWorktreeManager

router = APIRouter()
git_manager = GitWorktreeManager()


async def validate_git_repository(path: str) -> bool:
    """Validate if the path is a git repository."""
    return await git_manager.validate_repository(path)


@router.post("/", response_model=RepositorySchema, status_code=status.HTTP_201_CREATED)
async def create_repository(
    repository: RepositoryCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new repository."""
    # Validate path exists
    if not os.path.exists(repository.path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Path {repository.path} does not exist"
        )
    
    # Validate it's a git repository
    if not await validate_git_repository(repository.path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Path {repository.path} is not a git repository"
        )
    
    # Check if repository already exists
    query = select(Repository).where(Repository.path == repository.path)
    existing = await db.execute(query)
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Repository with this path already exists"
        )
    
    # Create repository
    db_repo = Repository(**repository.dict())
    db.add(db_repo)
    await db.commit()
    await db.refresh(db_repo)
    
    return db_repo


@router.get("/", response_model=List[RepositorySchema])
async def list_repositories(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List all repositories."""
    query = select(Repository).where(
        Repository.is_active == True
    ).offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{repository_id}", response_model=RepositorySchema)
async def get_repository(
    repository_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific repository by ID."""
    query = select(Repository).where(Repository.id == repository_id)
    result = await db.execute(query)
    repository = result.scalar_one_or_none()
    
    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )
    
    return repository


@router.patch("/{repository_id}", response_model=RepositorySchema)
async def update_repository(
    repository_id: UUID,
    repository_update: RepositoryUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update repository details."""
    query = select(Repository).where(Repository.id == repository_id)
    result = await db.execute(query)
    repository = result.scalar_one_or_none()
    
    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )
    
    # Update fields
    update_data = repository_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(repository, field, value)
    
    await db.commit()
    await db.refresh(repository)
    
    return repository


@router.delete("/{repository_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_repository(
    repository_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Soft delete a repository."""
    query = select(Repository).where(Repository.id == repository_id)
    result = await db.execute(query)
    repository = result.scalar_one_or_none()
    
    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )
    
    await repository.soft_delete(db)
    
    return None


@router.get("/{repository_id}/tasks", response_model=List[dict])
async def get_repository_tasks(
    repository_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get all tasks for a repository."""
    query = select(Repository).where(Repository.id == repository_id)
    result = await db.execute(query)
    repository = result.scalar_one_or_none()
    
    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )
    
    tasks = await repository.get_tasks(db)
    
    # Convert to dict for response
    return [
        {
            "id": str(task.id),
            "branch_name": task.branch_name,
            "status": task.status.value,
            "created_at": task.created_at.isoformat()
        }
        for task in tasks
    ]


import os