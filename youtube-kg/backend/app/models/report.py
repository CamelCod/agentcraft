import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ReportStatus(str, PyEnum):
    draft = "draft"
    generating = "generating"
    ready = "ready"
    error = "error"


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    config_json: Mapped[dict | None] = mapped_column(JSON)
    status: Mapped[ReportStatus] = mapped_column(String(50), default=ReportStatus.draft, nullable=False)
    # Storage keys per export format
    pdf_storage_key: Mapped[str | None] = mapped_column(Text)
    html_storage_key: Mapped[str | None] = mapped_column(Text)
    markdown_storage_key: Mapped[str | None] = mapped_column(Text)
    docx_storage_key: Mapped[str | None] = mapped_column(Text)
    json_storage_key: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    project: Mapped["Project"] = relationship("Project", back_populates="reports")
