import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class JobType(str, PyEnum):
    creator_discovery = "creator_discovery"
    domain_discovery = "domain_discovery"
    video_download = "video_download"
    transcription = "transcription"
    embedding = "embedding"
    knowledge_extraction = "knowledge_extraction"
    graph_construction = "graph_construction"
    verification = "verification"
    report_generation = "report_generation"


class JobStatus(str, PyEnum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)
    celery_task_id: Mapped[str | None] = mapped_column(String(255), index=True)
    type: Mapped[JobType] = mapped_column(String(50), nullable=False)
    status: Mapped[JobStatus] = mapped_column(String(50), default=JobStatus.pending, nullable=False)
    progress: Mapped[int] = mapped_column(default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped["Project"] = relationship("Project", back_populates="jobs")
