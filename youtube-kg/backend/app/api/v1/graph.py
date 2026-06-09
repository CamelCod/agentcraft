import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DB
from app.models import Project
from app.services import graph_service as graph

router = APIRouter(prefix="/projects/{project_id}/graph", tags=["graph"])


async def _assert_project_access(project_id: str, user_id: uuid.UUID, db) -> Project:
    result = await db.execute(
        select(Project).where(Project.id == uuid.UUID(project_id), Project.user_id == user_id)
    )
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    return p


@router.get("/overview")
async def graph_overview(project_id: str, current_user: CurrentUser, db: DB):
    await _assert_project_access(project_id, current_user.id, db)
    return graph.get_graph_overview(project_id)


@router.get("/claims")
async def list_claims(
    project_id: str,
    current_user: CurrentUser,
    db: DB,
    verification_status: str | None = None,
    min_confidence: float = 0.0,
    domain: str | None = None,
):
    await _assert_project_access(project_id, current_user.id, db)
    claims = graph.get_project_claims(project_id)

    filtered = [
        c for c in claims
        if (not verification_status or c.get("verification_status") == verification_status)
        and float(c.get("confidence_score") or 0) >= min_confidence
        and (not domain or c.get("domain") == domain)
    ]
    return filtered


@router.get("/claims/{claim_id}")
async def get_claim(project_id: str, claim_id: str, current_user: CurrentUser, db: DB):
    await _assert_project_access(project_id, current_user.id, db)
    claim = graph.get_claim_with_evidence(claim_id)
    if not claim:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Claim not found")
    return claim


@router.get("/contradictions")
async def list_contradictions(project_id: str, current_user: CurrentUser, db: DB):
    await _assert_project_access(project_id, current_user.id, db)
    driver = graph.get_driver()
    with driver.session() as session:
        result = session.run(
            """
            MATCH (a:Claim {project_id: $pid})-[r:CONTRADICTS]->(b:Claim)
            RETURN a.id AS claim_a_id, a.text AS claim_a_text,
                   b.id AS claim_b_id, b.text AS claim_b_text,
                   r.similarity_score AS similarity,
                   r.llm_reasoning AS reasoning
            LIMIT 100
            """,
            pid=str(project_id),
        )
        return [dict(r) for r in result]
