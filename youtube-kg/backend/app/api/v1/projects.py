import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DB
from app.models import Project, Creator, Video, DetectedDomain, Job, Report
from app.models.project import ProjectStatus
from app.models.job import JobStatus, JobType
from app.schemas.project import DomainApproveRequest, DomainOut, ProjectCreate, ProjectOut, ReportCreate

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(body: ProjectCreate, current_user: CurrentUser, db: DB):
    project = Project(
        user_id=current_user.id,
        name=body.name,
        creator_url=body.creator_url,
        status=ProjectStatus.discovering,
    )
    db.add(project)
    await db.flush()

    # Create a tracking job
    job = Job(
        project_id=project.id,
        type=JobType.creator_discovery,
        status=JobStatus.pending,
    )
    db.add(job)
    await db.flush()

    await db.commit()

    from app.workers.tasks.discovery import run_creator_discovery
    run_creator_discovery.delay(str(project.id), body.creator_url)

    return project


@router.get("", response_model=list[ProjectOut])
async def list_projects(current_user: CurrentUser, db: DB):
    result = await db.execute(
        select(Project).where(Project.user_id == current_user.id).order_by(Project.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project_id: str, current_user: CurrentUser, db: DB):
    project = await _get_project_or_404(project_id, current_user.id, db)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: str, current_user: CurrentUser, db: DB):
    project = await _get_project_or_404(project_id, current_user.id, db)
    await db.delete(project)


@router.get("/{project_id}/domains", response_model=list[DomainOut])
async def list_domains(project_id: str, current_user: CurrentUser, db: DB):
    await _get_project_or_404(project_id, current_user.id, db)
    result = await db.execute(
        select(DetectedDomain)
        .where(DetectedDomain.project_id == uuid.UUID(project_id))
        .order_by(DetectedDomain.confidence_score.desc())
    )
    return result.scalars().all()


@router.post("/{project_id}/domains/approve")
async def approve_domains(project_id: str, body: DomainApproveRequest, current_user: CurrentUser, db: DB):
    project = await _get_project_or_404(project_id, current_user.id, db)

    result = await db.execute(
        select(DetectedDomain).where(
            DetectedDomain.project_id == uuid.UUID(project_id)
        )
    )
    all_domains = result.scalars().all()

    domain_id_set = set(body.domain_ids)
    approved, rejected = 0, 0

    for d in all_domains:
        if str(d.id) in domain_id_set:
            d.status = "approved"
            d.approved_at = datetime.now(timezone.utc)
            approved += 1
        else:
            d.status = "rejected"
            rejected += 1

    project.status = ProjectStatus.ingesting

    # Determine which videos belong to approved domains and dispatch ingestion
    video_result = await db.execute(
        select(Video).where(Video.project_id == uuid.UUID(project_id))
    )
    videos = video_result.scalars().all()

    # For now, assign all videos to the first approved domain
    # (a more sophisticated approach would use cluster_data_json)
    approved_domains = [d for d in all_domains if str(d.id) in domain_id_set]
    if approved_domains and videos:
        domain_name = approved_domains[0].domain_name
        video_ids = []
        domain_map = {}
        for v in videos:
            v.assigned_domains = [domain_name]
            video_ids.append(str(v.id))
            domain_map[str(v.id)] = domain_name

        await db.commit()
        from app.workers.tasks.ingestion import launch_ingestion_pipeline
        launch_ingestion_pipeline(project_id, video_ids, domain_map)
        return {"approved": approved, "rejected": rejected}

    await db.commit()
    return {"approved": approved, "rejected": rejected}


@router.get("/{project_id}/videos")
async def list_videos(project_id: str, current_user: CurrentUser, db: DB, status: str | None = None):
    await _get_project_or_404(project_id, current_user.id, db)
    query = select(Video).where(Video.project_id == uuid.UUID(project_id))
    if status:
        query = query.where(Video.status == status)
    result = await db.execute(query.order_by(Video.published_at.desc()))
    videos = result.scalars().all()
    return [
        {
            "id": str(v.id),
            "youtube_id": v.youtube_id,
            "title": v.title,
            "status": v.status,
            "duration_seconds": v.duration_seconds,
            "published_at": str(v.published_at) if v.published_at else None,
            "error_message": v.error_message,
        }
        for v in videos
    ]


@router.get("/{project_id}/jobs")
async def list_jobs(project_id: str, current_user: CurrentUser, db: DB):
    await _get_project_or_404(project_id, current_user.id, db)
    result = await db.execute(
        select(Job).where(Job.project_id == uuid.UUID(project_id)).order_by(Job.created_at.desc()).limit(100)
    )
    jobs = result.scalars().all()
    return [
        {
            "id": str(j.id),
            "type": j.type,
            "status": j.status,
            "progress": j.progress,
            "started_at": str(j.started_at) if j.started_at else None,
            "completed_at": str(j.completed_at) if j.completed_at else None,
            "error_message": j.error_message,
        }
        for j in jobs
    ]


async def _get_project_or_404(project_id: str, user_id: uuid.UUID, db) -> Project:
    result = await db.execute(
        select(Project).where(
            Project.id == uuid.UUID(project_id),
            Project.user_id == user_id,
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    return project
