"""
Task chain 1: Creator Added → Discover Channel → Domain Discovery
"""
import uuid
from datetime import datetime, timezone

from celery import chain
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.config import get_settings
from app.services.creator_discovery import discover_channel, discover_videos
from app.services.domain_discovery import detect_domains
from app.workers.celery_app import celery_app

settings = get_settings()


def _get_sync_session() -> Session:
    engine = create_engine(settings.sync_database_url)
    return Session(engine)


@celery_app.task(
    bind=True,
    name="app.workers.tasks.discovery.run_creator_discovery",
    max_retries=3,
    default_retry_delay=30,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def run_creator_discovery(self, project_id: str, creator_url: str):
    from app.models import Creator, Video, Project, Job
    from app.models.project import ProjectStatus
    from app.models.video import VideoStatus
    from app.models.job import JobStatus

    with _get_sync_session() as session:
        # Update job status
        job = session.query(Job).filter(
            Job.project_id == uuid.UUID(project_id),
            Job.type == "creator_discovery",
            Job.status == "pending",
        ).first()
        if job:
            job.status = JobStatus.running
            job.started_at = datetime.now(timezone.utc)
            job.celery_task_id = self.request.id
            session.commit()

        try:
            channel = discover_channel(creator_url)

            # Upsert creator
            creator = session.query(Creator).filter_by(channel_id=channel.channel_id).first()
            if not creator:
                creator = Creator(
                    project_id=uuid.UUID(project_id),
                    channel_id=channel.channel_id,
                    channel_name=channel.channel_name,
                    channel_url=channel.channel_url,
                    description=channel.description,
                    subscriber_count=channel.subscriber_count,
                    video_count=channel.video_count,
                    thumbnail_url=channel.thumbnail_url,
                    country=channel.country,
                    metadata_json=channel.raw,
                )
                session.add(creator)
                session.flush()

            # Fetch videos and store metadata only
            videos = discover_videos(channel.channel_id)
            for v in videos:
                existing = session.query(Video).filter_by(
                    project_id=uuid.UUID(project_id),
                    youtube_id=v.youtube_id,
                ).first()
                if not existing:
                    session.add(Video(
                        creator_id=creator.id,
                        project_id=uuid.UUID(project_id),
                        youtube_id=v.youtube_id,
                        title=v.title,
                        description=v.description,
                        tags=v.tags,
                        duration_seconds=v.duration_seconds,
                        published_at=v.published_at,
                        thumbnail_url=v.thumbnail_url,
                        view_count=v.view_count,
                        status=VideoStatus.discovered,
                    ))

            # Update project status
            project = session.get(Project, uuid.UUID(project_id))
            if project:
                project.status = ProjectStatus.discovering

            if job:
                job.status = JobStatus.completed
                job.completed_at = datetime.now(timezone.utc)

            session.commit()

            # Trigger domain discovery
            chain(run_domain_discovery.s(project_id)).delay()

        except Exception as exc:
            if job:
                job.status = JobStatus.failed
                job.error_message = str(exc)[:500]
                session.commit()
            raise


@celery_app.task(
    bind=True,
    name="app.workers.tasks.discovery.run_domain_discovery",
    max_retries=2,
    default_retry_delay=60,
    autoretry_for=(Exception,),
)
def run_domain_discovery(self, project_id: str):
    from app.models import Video, Project, Job, DetectedDomain
    from app.models.project import ProjectStatus
    from app.models.job import JobStatus

    with _get_sync_session() as session:
        job = Job(
            project_id=uuid.UUID(project_id),
            type="domain_discovery",
            status=JobStatus.running,
            started_at=datetime.now(timezone.utc),
            celery_task_id=self.request.id,
        )
        session.add(job)
        session.flush()

        try:
            videos = session.query(Video).filter_by(project_id=uuid.UUID(project_id)).all()
            video_dicts = [
                {"title": v.title, "description": v.description or "", "tags": v.tags or []}
                for v in videos
            ]

            domains = detect_domains(video_dicts)

            for d in domains:
                session.add(DetectedDomain(
                    project_id=uuid.UUID(project_id),
                    domain_name=d.domain_name,
                    description=d.description,
                    confidence_score=d.confidence_score,
                    video_count=d.video_count,
                    representative_topics=d.representative_topics,
                    cluster_data_json={"video_percentage": d.video_percentage},
                ))

            project = session.get(Project, uuid.UUID(project_id))
            if project:
                project.status = ProjectStatus.domain_pending

            job.status = JobStatus.completed
            job.completed_at = datetime.now(timezone.utc)
            session.commit()

        except Exception as exc:
            job.status = JobStatus.failed
            job.error_message = str(exc)[:500]
            session.commit()
            raise


@celery_app.task(name="app.workers.tasks.discovery.health_check")
def health_check():
    return {"status": "ok"}
