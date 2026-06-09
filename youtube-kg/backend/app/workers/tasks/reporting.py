from app.workers.celery_app import celery_app


@celery_app.task(
    bind=True,
    name="app.workers.tasks.reporting.generate_report",
    queue="reporting",
    max_retries=2,
    autoretry_for=(Exception,),
)
def generate_report_task(self, report_id: str, project_id: str, config: dict):
    import uuid
    from datetime import datetime, timezone
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from app.config import get_settings
    from app.models import Report, Creator, Video
    from app.models.report import ReportStatus
    from app.services import reporting

    settings = get_settings()
    engine = create_engine(settings.sync_database_url)

    with Session(engine) as session:
        report = session.get(Report, uuid.UUID(report_id))
        if not report:
            raise ValueError(f"Report {report_id} not found")

        report.status = ReportStatus.generating
        session.commit()

        try:
            creator = session.query(Creator).filter_by(
                project_id=uuid.UUID(project_id)
            ).first()
            creator_meta = {
                "channel_name": creator.channel_name if creator else "Unknown",
                "channel_id": creator.channel_id if creator else "",
                "thumbnail_url": creator.thumbnail_url if creator else "",
            }

            videos = session.query(Video).filter_by(project_id=uuid.UUID(project_id)).all()
            video_dicts = [
                {
                    "youtube_id": v.youtube_id,
                    "title": v.title,
                    "published_at": str(v.published_at) if v.published_at else "",
                    "duration_seconds": v.duration_seconds,
                }
                for v in videos
            ]

            report_data = reporting.assemble_report(
                project_id=project_id,
                report_id=report_id,
                config=config,
                creator_meta=creator_meta,
                videos=video_dicts,
            )

            formats = config.get("formats", ["json", "html", "pdf", "markdown", "docx"])
            storage_keys = reporting.upload_all_formats(report_data, report_id, project_id, formats)

            report.pdf_storage_key = storage_keys.get("pdf")
            report.html_storage_key = storage_keys.get("html")
            report.markdown_storage_key = storage_keys.get("markdown")
            report.docx_storage_key = storage_keys.get("docx")
            report.json_storage_key = storage_keys.get("json")
            report.status = ReportStatus.ready
            report.completed_at = datetime.now(timezone.utc)
            session.commit()

            return {"report_id": report_id, "formats": list(storage_keys.keys())}

        except Exception as exc:
            report.status = ReportStatus.error
            session.commit()
            raise
