import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DB
from app.models import Project, Report
from app.models.report import ReportStatus
from app.schemas.project import ReportCreate

router = APIRouter(prefix="/reports", tags=["reports"])

FORMAT_KEY_MAP = {
    "pdf": "pdf_storage_key",
    "html": "html_storage_key",
    "markdown": "markdown_storage_key",
    "md": "markdown_storage_key",
    "docx": "docx_storage_key",
    "json": "json_storage_key",
}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_report(body: ReportCreate, current_user: CurrentUser, db: DB):
    result = await db.execute(
        select(Project).where(
            Project.id == uuid.UUID(body.project_id),
            Project.user_id == current_user.id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")

    report = Report(
        project_id=uuid.UUID(body.project_id),
        title=body.title,
        config_json=body.config,
        status=ReportStatus.draft,
    )
    db.add(report)
    await db.flush()
    await db.commit()

    from app.workers.tasks.reporting import generate_report_task
    generate_report_task.delay(str(report.id), body.project_id, body.config)

    return {"report_id": str(report.id), "status": "queued"}


@router.get("")
async def list_reports(current_user: CurrentUser, db: DB, project_id: str | None = None):
    query = (
        select(Report)
        .join(Project, Report.project_id == Project.id)
        .where(Project.user_id == current_user.id)
        .order_by(Report.created_at.desc())
    )
    if project_id:
        query = query.where(Report.project_id == uuid.UUID(project_id))
    result = await db.execute(query)
    reports = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "project_id": str(r.project_id),
            "title": r.title,
            "status": r.status,
            "available_formats": [
                fmt for fmt, key in FORMAT_KEY_MAP.items()
                if getattr(r, key, None)
            ],
            "created_at": str(r.created_at),
            "completed_at": str(r.completed_at) if r.completed_at else None,
        }
        for r in reports
    ]


@router.get("/{report_id}/download/{format}")
async def download_report(report_id: str, format: str, current_user: CurrentUser, db: DB):
    result = await db.execute(
        select(Report)
        .join(Project, Report.project_id == Project.id)
        .where(Report.id == uuid.UUID(report_id), Project.user_id == current_user.id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Report not found")

    key_attr = FORMAT_KEY_MAP.get(format)
    if not key_attr:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unknown format: {format}")

    storage_key = getattr(report, key_attr, None)
    if not storage_key:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Format {format} not available yet")

    from app.config import get_settings
    from app.core.storage import get_presigned_url
    settings = get_settings()
    url = get_presigned_url(settings.minio_bucket_reports, storage_key, expires_in=3600)
    # Return the pre-signed URL as JSON so the frontend can open it after
    # authenticating this request — a plain anchor would bypass the bearer token.
    return {"url": url, "format": format, "expires_in": 3600}
