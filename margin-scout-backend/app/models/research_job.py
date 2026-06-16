import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Enum, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.ext.mutable import MutableDict
import json
from sqlalchemy.types import TypeDecorator, VARCHAR
from app.db.base import Base

class JobStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"

class JSONEncodedDict(TypeDecorator):
    impl = VARCHAR
    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return json.dumps(value)
    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return json.loads(value)

class ResearchJob(Base):
    __tablename__ = "research_jobs"
    __table_args__ = {'extend_existing': True}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    title = Column(String(255), nullable=True)
    status = Column(Enum(JobStatus), default=JobStatus.pending, nullable=False)
    
    progress = Column(Integer, default=0)
    total_items = Column(Integer, default=0)
    matched_items = Column(Integer, default=0)
    
    conditions = Column(MutableDict.as_mutable(JSONEncodedDict), nullable=True)
    result_summary = Column(MutableDict.as_mutable(JSONEncodedDict), nullable=True)
    
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="research_jobs")
