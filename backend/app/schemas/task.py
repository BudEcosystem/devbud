from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskBase(BaseModel):
    repository_id: UUID
    branch_name: str = Field(..., min_length=1, max_length=100)
    instructions: str = Field(..., min_length=1)
    
    @validator("branch_name")
    def validate_branch_name(cls, v):
        # Ensure branch name is valid for git
        invalid_chars = [' ', '~', '^', ':', '?', '*', '[', '\\']
        for char in invalid_chars:
            if char in v:
                raise ValueError(f"Branch name cannot contain '{char}'")
        return v


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    status: Optional[TaskStatus] = None
    output: Optional[str] = None
    error_message: Optional[str] = None


class TaskInDB(TaskBase):
    id: UUID
    status: TaskStatus
    worktree_path: Optional[str] = None
    output: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class Task(TaskInDB):
    repository: Optional[Dict[str, Any]] = None  # Simplified repository info
    
    @validator('repository', pre=True, always=True)
    def serialize_repository(cls, v):
        if hasattr(v, 'id'):  # It's a Repository object
            return {
                "id": str(v.id),
                "name": v.name
            }
        return v


class TaskOutput(BaseModel):
    task_id: UUID
    output: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)