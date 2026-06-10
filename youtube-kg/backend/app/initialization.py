"""App initialization: migrations and service setup."""
import asyncio
import logging
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)


async def run_migrations() -> bool:
    """Run Alembic migrations. Returns True if successful."""
    try:
        logger.info("Starting database migrations...")
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd="/app",
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            logger.info("Database migrations completed successfully")
            return True
        else:
            logger.warning(f"Migrations failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        logger.warning("Database migrations timed out after 60 seconds")
        return False
    except Exception as e:
        logger.warning(f"Could not run migrations: {e}")
        return False


async def ensure_graph_setup() -> bool:
    """Ensure Neo4j constraints exist. Returns True if successful."""
    try:
        logger.info("Setting up Neo4j constraints...")
        from app.services.graph_service import ensure_constraints

        ensure_constraints()
        logger.info("Neo4j constraints created successfully")
        return True
    except Exception as e:
        logger.warning(f"Could not set up Neo4j: {e}")
        return False


async def ensure_qdrant_setup() -> bool:
    """Ensure Qdrant collections exist. Returns True if successful."""
    try:
        logger.info("Setting up Qdrant collections...")
        from app.services.memory import ensure_collections

        ensure_collections()
        logger.info("Qdrant collections created successfully")
        return True
    except Exception as e:
        logger.warning(f"Could not set up Qdrant: {e}")
        return False


async def create_initial_superuser() -> bool:
    """Create initial superuser if not present. Returns True if successful."""
    try:
        from app.config import get_settings
        from app.database import AsyncSessionLocal
        from app.models.user import User, UserRole
        from app.core.security import hash_password
        from sqlalchemy import select

        settings = get_settings()

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(User).where(User.email == settings.first_superuser_email)
            )
            user = result.scalar_one_or_none()

            if not user:
                logger.info("Creating initial superuser...")
                user = User(
                    email=settings.first_superuser_email,
                    hashed_password=hash_password(settings.first_superuser_password),
                    role=UserRole.admin,
                    full_name="Admin",
                )
                session.add(user)
                await session.commit()
                logger.info("Initial superuser created successfully")
            else:
                logger.info("Initial superuser already exists")

            return True
    except Exception as e:
        logger.warning(f"Could not create initial superuser: {e}")
        return False


async def initialize_app(skip_migrations: bool = False) -> dict:
    """
    Initialize app: run migrations and set up services in parallel.

    Returns dict with initialization status:
    {
        'migrations': bool,
        'graph': bool,
        'qdrant': bool,
        'superuser': bool,
        'success': bool  # True if all tasks completed (may still have individual failures)
    }
    """
    logger.info("Starting app initialization...")

    # Run migrations first (sequentially, must happen before other operations)
    migrations_ok = True
    if not skip_migrations:
        migrations_ok = await run_migrations()
    else:
        logger.info("Skipping migrations as requested")

    # Run other initialization tasks in parallel
    graph_ok, qdrant_ok, superuser_ok = await asyncio.gather(
        ensure_graph_setup(),
        ensure_qdrant_setup(),
        create_initial_superuser(),
        return_exceptions=False,
    )

    status = {
        "migrations": migrations_ok,
        "graph": graph_ok,
        "qdrant": qdrant_ok,
        "superuser": superuser_ok,
        "success": True,  # All tasks completed, regardless of individual success
    }

    logger.info(f"App initialization complete: {status}")
    return status


async def background_initialize(skip_migrations: bool = False) -> dict:
    """Run initialization in background (non-blocking). Logs and returns results."""
    try:
        result = await initialize_app(skip_migrations=skip_migrations)
        return result
    except Exception as e:
        logger.error(f"Background initialization failed: {e}")
        return {
            "migrations": False,
            "graph": False,
            "qdrant": False,
            "superuser": False,
            "success": False,
            "error": str(e),
        }
