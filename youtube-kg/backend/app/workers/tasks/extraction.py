from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.tasks.extraction.finalize_ingestion")
def finalize_ingestion(results, project_id: str):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from app.config import get_settings
    from app.models import Project
    from app.models.project import ProjectStatus

    settings = get_settings()
    engine = create_engine(settings.sync_database_url)
    with Session(engine) as session:
        import uuid
        project = session.get(Project, uuid.UUID(project_id))
        if project:
            project.status = ProjectStatus.ready
            session.commit()

    return {"project_id": project_id, "status": "ingestion_complete"}
