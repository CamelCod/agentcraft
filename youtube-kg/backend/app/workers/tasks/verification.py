from app.workers.celery_app import celery_app


@celery_app.task(
    bind=True,
    name="app.workers.tasks.verification.run_verification",
    queue="verification",
    max_retries=2,
    autoretry_for=(Exception,),
)
def run_verification_task(self, project_id: str):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from app.config import get_settings
    from app.models import Job
    from app.models.job import JobStatus
    from app.services.verification import run_verification
    import uuid
    from datetime import datetime, timezone

    settings = get_settings()
    engine = create_engine(settings.sync_database_url)

    with Session(engine) as session:
        job = Job(
            project_id=uuid.UUID(project_id),
            type="verification",
            status=JobStatus.running,
            started_at=datetime.now(timezone.utc),
            celery_task_id=self.request.id,
        )
        session.add(job)
        session.flush()

        try:
            stats = run_verification(project_id)
            job.status = JobStatus.completed
            job.completed_at = datetime.now(timezone.utc)
            job.metadata_json = stats
            session.commit()
            return stats
        except Exception as exc:
            job.status = JobStatus.failed
            job.error_message = str(exc)[:500]
            session.commit()
            raise
