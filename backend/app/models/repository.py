from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import uuid

from app.core.database import Base


class Repository(Base):
    __tablename__ = "repositories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    path = Column(String, nullable=False, unique=True)
    default_branch = Column(String(100), nullable=False, default="main")
    description = Column(Text, nullable=True)
    
    # Soft delete fields
    is_active = Column(Boolean, default=True, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tasks = relationship("Task", back_populates="repository", lazy="selectin")
    
    async def get_tasks(self, db: AsyncSession):
        """Get all tasks for this repository."""
        from app.models.task import Task
        
        query = select(Task).where(
            Task.repository_id == self.id,
            Task.is_active == True
        )
        result = await db.execute(query)
        return result.scalars().all()
    
    async def soft_delete(self, db: AsyncSession):
        """Soft delete the repository."""
        self.is_active = False
        self.deleted_at = datetime.utcnow()
        db.add(self)
        await db.commit()
        await db.refresh(self)