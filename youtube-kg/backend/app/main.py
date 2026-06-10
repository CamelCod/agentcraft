import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.v1 import auth, projects, graph, verification, reports
from app.config import get_settings
from app.database import engine
from app.models import Base

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    import asyncio

    # Start initialization in background - don't block app startup
    initialization_task = asyncio.create_task(
        _background_init()
    )

    # Store task and result in app state for monitoring
    app.state.initialization_task = initialization_task
    app.state.initialization_result = None

    yield

    # Wait for initialization to complete on shutdown (graceful cleanup)
    try:
        app.state.initialization_result = await asyncio.wait_for(initialization_task, timeout=5.0)
    except asyncio.TimeoutError:
        logger.warning("App initialization still running during shutdown")
        app.state.initialization_result = {"success": False, "error": "Timeout during shutdown"}
    except Exception as e:
        logger.warning(f"App initialization failed: {e}")
        app.state.initialization_result = {"success": False, "error": str(e)}


async def _background_init() -> None:
    """Background initialization task. Doesn't block app startup."""
    import asyncio
    import logging

    logger = logging.getLogger(__name__)

    try:
        # Give the app a moment to start serving before we start heavy operations
        await asyncio.sleep(1)

        from app.initialization import background_initialize

        await background_initialize(skip_migrations=False)
    except Exception as e:
        logger.error(f"Background initialization failed: {e}")


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


@app.get("/initialization-status")
async def initialization_status():
    """Check app initialization status."""
    task = getattr(app.state, "initialization_task", None)
    stored_result = getattr(app.state, "initialization_result", None)

    if task is None:
        return {"status": "not_started"}

    if task.done():
        try:
            result = stored_result or task.result()
            if result:
                return {
                    "status": "completed",
                    "details": result,
                }
            else:
                return {
                    "status": "completed",
                    "message": "Initialization completed",
                }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
            }
    else:
        return {
            "status": "initializing",
            "message": "App is initializing services in the background",
        }
