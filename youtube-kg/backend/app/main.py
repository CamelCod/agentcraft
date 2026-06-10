from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.v1 import auth, projects, graph, verification, reports
from app.config import get_settings
from app.database import engine
from app.models import Base

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Skip heavy initialization on startup - allow app to start immediately
    # These can be initialized on-demand or via background tasks
    yield


app = FastAPI(
    title="YouTube Creator Knowledge Graph API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# Routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(projects.router, prefix="/api/v1")
app.include_router(graph.router, prefix="/api/v1")
app.include_router(verification.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}
