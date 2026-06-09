from datetime import datetime
from pydantic import BaseModel, HttpUrl


class ProjectCreate(BaseModel):
    name: str
    creator_url: str


class ProjectOut(BaseModel):
    id: str
    name: str
    creator_url: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DomainOut(BaseModel):
    id: str
    domain_name: str
    description: str | None
    confidence_score: float
    video_count: int
    representative_topics: list | None
    status: str

    class Config:
        from_attributes = True


class DomainApproveRequest(BaseModel):
    domain_ids: list[str]


class ReportCreate(BaseModel):
    project_id: str
    title: str
    config: dict = {}
