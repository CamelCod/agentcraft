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
    # Create PostgreSQL tables on startup
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        # Schema may already exist or be partially set up
        # Continue anyway - migrations will handle proper schema management
        print(f"Warning: Could not create tables on startup: {e}")

    # Ensure Neo4j constraints exist
    try:
        from app.services.graph_service import ensure_constraints
        ensure_constraints()
    except Exception:
        pass

    # Ensure Qdrant collections exist
    try:
        from app.services.memory import ensure_collections
        ensure_collections()
    except Exception:
        pass

    # Create first superuser if not present
    try:
        from app.database import AsyncSessionLocal
        from sqlalchemy import select
        from app.models.user import User, UserRole
        from app.core.security import hash_password
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).where(User.email == settings.first_superuser_email))
            if not result.scalar_one_or_none():
                session.add(User(
                    email=settings.first_superuser_email,
                    hashed_password=hash_password(settings.first_superuser_password),
                    role=UserRole.admin,
                    full_name="Admin",
                ))
                await session.commit()
    except Exception as e:
        print(f"Warning: Could not create initial superuser: {e}")

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
