from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID
import os


class RepositoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    path: str = Field(..., min_length=1)
    default_branch: str = Field(default="main", min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    
    @validator("path")
    def validate_path(cls, v):
        # Expand user path
        expanded_path = os.path.expanduser(v)
        return os.path.abspath(expanded_path)


class RepositoryCreate(RepositoryBase):
    pass


class RepositoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    default_branch: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class RepositoryInDB(RepositoryBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class Repository(RepositoryInDB):
    task_count: Optional[int] = 0
    active_task_count: Optional[int] = 0