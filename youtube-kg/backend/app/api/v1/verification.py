import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DB
from app.models import Project, Job
from app.models.job import JobStatus, JobType

router = APIRouter(prefix="/projects/{project_id}/verify", tags=["verification"])


@router.post("")
async def trigger_verification(project_id: str, current_user: CurrentUser, db: DB):
    result = await db.execute(
        select(Project).where(Project.id == uuid.UUID(project_id), Project.user_id == current_user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")

    job = Job(
        project_id=uuid.UUID(project_id),
        type=JobType.verification,
        status=JobStatus.pending,
    )
    db.add(job)
    await db.flush()
    await db.commit()

    from app.workers.tasks.verification import run_verification_task
    run_verification_task.delay(project_id, str(job.id))

    return {"job_id": str(job.id), "status": "queued"}
