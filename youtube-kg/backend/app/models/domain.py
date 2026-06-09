import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DomainStatus(str, PyEnum):
    detected = "detected"
    approved = "approved"
    rejected = "rejected"
    processing = "processing"
    completed = "completed"


class DetectedDomain(Base):
    __tablename__ = "detected_domains"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)
    domain_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    video_count: Mapped[int] = mapped_column(default=0)
    representative_topics: Mapped[list | None] = mapped_column(JSON)
    cluster_data_json: Mapped[dict | None] = mapped_column(JSON)
    status: Mapped[DomainStatus] = mapped_column(String(50), default=DomainStatus.detected, nullable=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    project: Mapped["Project"] = relationship("Project", back_populates="detected_domains")
