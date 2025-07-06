from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repository_id = Column(UUID(as_uuid=True), ForeignKey("repositories.id"), nullable=False)
    branch_name = Column(String(100), nullable=False)
    instructions = Column(Text, nullable=False)
    status = Column(SQLEnum(TaskStatus), nullable=False, default=TaskStatus.PENDING)
    worktree_path = Column(String, nullable=True)
    output = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    
    # Relationships
    repository = relationship("Repository", back_populates="tasks")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('repository_id', 'branch_name', 
                        name='_repo_branch_uc'),
    )
    
    async def start(self, db: AsyncSession, worktree_path: str):
        """Start the task execution."""
        if self.status != TaskStatus.PENDING:
            raise ValueError(f"Cannot start task in {self.status} status")
        
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.utcnow()
        self.worktree_path = worktree_path
        self.output = f"Task started at {self.started_at}\n"
        
        db.add(self)
        await db.commit()
        await db.refresh(self)
    
    async def complete(self, db: AsyncSession, success: bool, output: str = ""):
        """Complete the task execution."""
        if self.status != TaskStatus.RUNNING:
            raise ValueError(f"Cannot complete task in {self.status} status")
        
        self.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
        self.completed_at = datetime.utcnow()
        if output:
            self.output = (self.output or "") + f"\n{output}\n"
        self.output = (self.output or "") + f"Task {'completed' if success else 'failed'} at {self.completed_at}\n"
        
        db.add(self)
        await db.commit()
        await db.refresh(self)
    
    async def cancel(self, db: AsyncSession, reason: str = ""):
        """Cancel the task execution."""
        if self.status not in [TaskStatus.PENDING, TaskStatus.RUNNING]:
            raise ValueError(f"Cannot cancel task in {self.status} status")
        
        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        self.output = (self.output or "") + f"\nTask cancelled at {self.completed_at}\n"
        if reason:
            self.output = (self.output or "") + f"Reason: {reason}\n"
        
        db.add(self)
        await db.commit()
        await db.refresh(self)
    
    async def append_output(self, db: AsyncSession, output: str):
        """Append output to the task log."""
        self.output = (self.output or "") + f"{output}\n"
        db.add(self)
        await db.commit()
        await db.refresh(self)