import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ProjectStatus(str, PyEnum):
    created = "created"
    discovering = "discovering"
    domain_pending = "domain_pending"
    ingesting = "ingesting"
    extracting = "extracting"
    verifying = "verifying"
    ready = "ready"
    archived = "archived"
    error = "error"


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    creator_url: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ProjectStatus] = mapped_column(String(50), default=ProjectStatus.created, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    owner: Mapped["User"] = relationship("User", back_populates="projects")
    creator: Mapped["Creator | None"] = relationship("Creator", back_populates="project", uselist=False)
    detected_domains: Mapped[list["DetectedDomain"]] = relationship("DetectedDomain", back_populates="project")
    jobs: Mapped[list["Job"]] = relationship("Job", back_populates="project")
    reports: Mapped[list["Report"]] = relationship("Report", back_populates="project")
