# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

YouTube Creator Knowledge Graph is a self-hosted SaaS platform that converts YouTube creator URLs into verified knowledge graphs and citation-backed reports. The system uses LLMs to extract knowledge from video transcripts, builds a Neo4j graph, and generates multi-format reports (PDF, HTML, Markdown, DOCX, JSON).

## Architecture at a Glance

```
Client Browser (React)
    ↓
Nginx reverse proxy (:80)
    ├→ FastAPI backend (:8000) — auth, projects, graph APIs
    ├→ Frontend dev/build (:3000)
    └→ Auxiliary services (Flower, MinIO console)

FastAPI Backend
    ├→ PostgreSQL — relational state (users, projects, settings)
    ├→ Neo4j — knowledge graph (entities, relationships, claims)
    ├→ Qdrant — vector embeddings (semantic search)
    ├→ Redis — task broker
    └→ MinIO — object storage (transcripts, reports)

Celery Worker + Beat
    ├→ yt-dlp — download videos
    ├→ Whisper — transcription (separate service :9002)
    ├→ LLM (Anthropic/OpenAI) — domain/knowledge extraction
    └→ Verification + Report generation
```

**Key Data Flow:**
1. User creates project with YouTube URL
2. Worker downloads video metadata, triggers domain discovery (LLM)
3. User selects domains → worker ingests audio, transcribes, extracts knowledge
4. Graph built incrementally in Neo4j; verification runs cross-video claim scoring
5. Report generation exports graph with citations

## Quick Commands

### Backend (FastAPI)

```bash
# Development (hot-reload, outside Docker)
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Run unit tests
cd backend
pytest tests/unit/ -v

# Run a single test
pytest tests/unit/test_something.py::TestClass::test_method -v

# Run with coverage
pytest --cov=app --cov-report=html

# Lint (eslint for frontend, no backend linter currently)
cd frontend
npm run lint
```

### Frontend (React + Vite)

```bash
# Development server
cd frontend
npm install
npm run dev

# Build for production
npm run build

# Linting
npm run lint
```

### Docker & Services

```bash
# Start all services (PostgreSQL, Neo4j, Redis, etc.)
docker compose up -d

# View logs
docker compose logs -f api        # FastAPI
docker compose logs -f worker     # Celery worker
docker compose logs -f beat       # Scheduler
docker compose logs -f whisper    # Transcription service

# Access services
# API docs: http://localhost/api/docs
# Flower (Celery monitor): http://localhost/flower
# MinIO console: http://localhost/minio
# Grafana: http://localhost:3000 (internal; credentials from .env)
```

### Database Migrations

```bash
# Generate new migration (after changing models)
cd backend
alembic revision --autogenerate -m "description"

# Apply pending migrations
alembic upgrade head

# Revert one migration
alembic downgrade -1
```

## Backend Structure

```
backend/
├── app/
│   ├── api/v1/              # API routers (auth, projects, graph, reports, verification)
│   ├── core/                # Security, config, logging
│   ├── models/              # SQLAlchemy models (User, Project, Video, etc.)
│   ├── schemas/             # Pydantic request/response schemas
│   ├── services/            # Business logic
│   │   ├── domain_discovery.py      # LLM clustering of video domains
│   │   ├── knowledge_extraction.py  # Extract claims from transcripts
│   │   ├── graph_service.py         # Neo4j CRUD and querying
│   │   ├── verification.py          # Cross-video claim scoring
│   │   ├── reporting.py             # Report generation
│   │   ├── llm.py                   # LLM provider abstraction (Anthropic/OpenAI)
│   │   ├── transcription.py         # Whisper integration
│   │   └── memory.py                # Qdrant vector store for semantic search
│   ├── workers/             # Celery task definitions
│   │   └── tasks/           # Task implementations (discovery, ingestion, verification, etc.)
│   ├── config.py            # Settings (env vars via pydantic-settings)
│   ├── database.py          # SQLAlchemy engine and session factories
│   └── main.py              # FastAPI app definition, lifespan hooks
├── tests/
│   ├── unit/                # Fast, isolated tests
│   ├── integration/         # Tests hitting real databases (optional)
│   └── conftest.py          # pytest fixtures
├── pytest.ini               # Coverage 70% minimum, asyncio_mode=auto
├── Dockerfile               # Multi-stage: dependencies, dev, production
└── requirements.txt         # All dependencies (see groups: web, db, llm, workers, test)
```

**Key Patterns:**
- **Services** contain business logic; routers delegate to services
- **Models** define PostgreSQL schema; graph nodes are separate in Neo4j
- **Async/await throughout** — FastAPI uses asyncio; Celery tasks are sync (workers run in separate processes)
- **Dependency injection** via `api/deps.py` — session, auth user, etc. are injected into handlers
- **Config via environment** — see `.env.example` for required vars (YOUTUBE_API_KEY, LLM secrets, DB credentials, etc.)

## Frontend Structure

```
frontend/src/
├── App.tsx                  # Root component, routing setup
├── pages/                   # Page-level components (Project, Dashboard, etc.)
├── components/              # Reusable UI components
├── api/                     # Axios API client helpers
├── store/                   # Zustand state management
└── index.css                # Tailwind styles
```

**Stack:** React 18, TypeScript, Vite, Tailwind CSS, Radix UI, TanStack Query (React Query), react-force-graph-2d (knowledge graph visualization).

**Key Patterns:**
- Components are functional + hooks (React Query for server state, Zustand for client state)
- API calls via `axios` with error handling; queries are in `api/` folder
- Graph visualization uses `react-force-graph-2d` for real-time node/link rendering
- All request/response types should match backend schemas

## Database & ORM

**PostgreSQL (via SQLAlchemy):**
- User management, project metadata, video ingestion state, report outputs
- Migrations managed by Alembic; run `alembic upgrade head` on startup (handled by Docker entrypoint)
- Async sessions via `AsyncSessionLocal` from `database.py`

**Neo4j (Knowledge Graph):**
- Entities (Person, Organization, Concept, etc.) as nodes
- Relationships (cited_by, related_to, mentioned_in, etc.) with properties
- No schema migrations; constraints are enforced at app startup via `ensure_constraints()` in `graph_service.py`
- Queries use py2neo or raw Cypher via `neo4j` driver; abstracted in `services/graph_service.py`

**Qdrant (Vector Embeddings):**
- Stores sentence-transformer embeddings of claims for semantic search
- Collections created on app startup via `ensure_collections()` in `services/memory.py`
- Used for finding similar claims across videos during verification

## Celery Task Queue

**Tasks are defined in `backend/app/workers/tasks/` and triggered via FastAPI routers.**

Queue assignments (see docker-compose.yml worker command):
- `default` — general tasks
- `discovery` — domain discovery (LLM clustering)
- `ingestion` — video download, transcription
- `extraction` — knowledge extraction from transcripts
- `verification` — cross-video verification
- `reporting` — report generation

**Key Files:**
- `celery_app.py` — Celery app config, Redis broker setup
- `tasks/__init__.py` — Task definitions; each task is a decorated function
- `workers/beat.py` — Celery Beat scheduler for periodic tasks (optional cleanup, etc.)

**Important:** Celery tasks are **synchronous** (run in separate worker process), but they call async services. Wrap async calls using `asyncio.run()` if needed.

## Environment Variables

See `.env.example` for full list. Critical ones:

- `YOUTUBE_API_KEY` — YouTube Data API v3 key (required for video metadata)
- `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` — LLM provider secret
- `LLM_PROVIDER` — "anthropic" (default) or "openai"
- `DATABASE_URL` — PostgreSQL connection string (docker default: `postgresql+asyncpg://user:pass@postgres/db`)
- `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` — Neo4j connection
- `REDIS_URL` — Redis broker (docker default: `redis://redis:6379`)
- `QDRANT_URL` — Qdrant vector store (docker default: `http://qdrant:6333`)
- `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY` — Object storage
- `FIRST_SUPERUSER_EMAIL`, `FIRST_SUPERUSER_PASSWORD` — Initial admin user (created on startup if not present)
- `CORS_ORIGINS` — Comma-separated allowed origins
- `DEVICE` — "cpu" or "cuda" (affects Whisper performance)

**Development:** Copy `.env.example` → `.env` and edit passwords/keys. Docker Compose reads from `.env` automatically.

## Testing Strategy

- **pytest** with `asyncio_mode=auto` for async tests
- Coverage target: 70% (enforced via `pytest.ini`)
- Unit tests in `tests/unit/` — mock external services (DB, LLM, etc.)
- Fixtures in `conftest.py` — override session, auth, mocks

**Run tests:**
```bash
cd backend
pytest                           # All tests
pytest -k "test_domain"         # Filter by name
pytest tests/unit/test_api.py   # Single file
pytest -x                        # Stop at first failure
pytest --pdb                     # Drop into debugger on failure
```

## Key Services & Their Responsibilities

| Service | Purpose | Entry Point |
|---------|---------|-------------|
| `domain_discovery.py` | LLM-powered clustering of video topics | Workers task; calls LLM |
| `knowledge_extraction.py` | Extract entities/claims from transcripts | Workers task; calls LLM |
| `graph_service.py` | Neo4j CRUD: create/query nodes, relationships | Called by extraction, verification, API |
| `verification.py` | Cross-video claim scoring and conflict detection | Workers task; queries Neo4j |
| `reporting.py` | Generate PDF/HTML/Markdown/DOCX/JSON reports | API endpoint; queries Neo4j + DB |
| `transcription.py` | Coordinate Whisper transcription (external service) | Workers task; HTTP calls |
| `llm.py` | LLM provider abstraction (Anthropic/OpenAI) | Called by domain_discovery, knowledge_extraction |
| `memory.py` | Qdrant vector store: store/search embeddings | Called by knowledge_extraction, verification |

## Common Modifications

**Adding a new API endpoint:**
1. Create schema in `app/schemas/something.py` (Pydantic models for request/response)
2. Add database model in `app/models/something.py` (SQLAlchemy) if needed
3. Create service method in `app/services/something.py` (business logic)
4. Add router in `app/api/v1/something.py` (HTTP endpoints)
5. Include router in `app/main.py` — `app.include_router(something.router, prefix="/api/v1")`

**Adding a new Celery task:**
1. Create task function in `app/workers/tasks/something.py` (decorate with `@celery_app.task`)
2. Call from API endpoint or other task using `.delay()` or `.apply_async()`
3. Monitor via Flower at `http://localhost/flower`

**Adding a database migration:**
1. Modify SQLAlchemy model in `app/models/`
2. Run `alembic revision --autogenerate -m "description"`
3. Review generated migration in `alembic/versions/`
4. Test: `alembic upgrade head` (or `downgrade -1` to revert)

**Updating the knowledge graph schema (Neo4j):**
1. Modify constraint/index definitions in `graph_service.py` — `ensure_constraints()`
2. Changes are idempotent; re-running `ensure_constraints()` won't harm existing data
3. For data migrations, write manual Cypher scripts in workers or directly via neo4j driver

## Observability

- **Logs:** Structured logging via `structlog`; output to stdout (Docker captures)
- **Metrics:** Prometheus via `prometheus-fastapi-instrumentator`; exposed at `/metrics`
- **Grafana:** Dashboard at `http://localhost:3000` (internal only; credentials in `.env`)
- **Celery Monitor:** Flower at `http://localhost/flower` — task history, worker stats, queues

## Deployment Notes

- **Docker image** built in two stages (dev with dev dependencies, production with minimal runtime)
- **Health checks** on API (`/health` endpoint) and PostgreSQL; services restart on unhealthy state
- **Volumes:** Backend and frontend code mounted for hot-reload in development
- **Networks:** `public` (nginx exposed) and `internal` (service-to-service); Redis, Neo4j, PostgreSQL are internal only
- **Production:** Use `docker compose -f docker-compose.yml -f docker-compose.prod.yml` (if exists) or set `target: production` in Dockerfile build

## Git & Branching

- Current working branch: `claude/youtube-creator-knowledge-graph-d9a8o1`
- Main branch: `main`
- Recent fixes: bcrypt truncation, Neo4j env var encoding, import exports, missing dependencies (requests, python-multipart)
