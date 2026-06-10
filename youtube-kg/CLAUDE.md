# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

YouTube Creator Knowledge Graph is a SaaS platform that converts YouTube creator URLs into verified knowledge graphs and citation-backed reports. The system uses LLMs to extract knowledge from video transcripts, builds a Neo4j graph, and generates multi-format reports (PDF, HTML, Markdown, DOCX, JSON).

## Current Deployment Architecture

**Production:**
```
User Browser → Vercel (Next.js Frontend)
                    ↓
              Supabase Auth (JWT)
                    ↓
              Fly.io (FastAPI Backend) → External Services:
                ├→ Supabase PostgreSQL
                ├→ Neo4j (managed or self-hosted)
                ├→ Qdrant (vector DB)
                ├→ Redis (message broker)
                └→ Object storage (S3/MinIO)
```

**Local Development (Docker Compose):**
```
Client Browser (Next.js dev server :3000)
    ↓
Next.js API Routes (:3000/api)
    ↓
FastAPI Backend (:8000 in Docker)
    ├→ PostgreSQL
    ├→ Neo4j
    ├→ Qdrant
    ├→ Redis
    └→ MinIO

Celery Workers (Docker)
    ├→ yt-dlp — download videos
    ├→ Whisper service — transcription
    ├→ LLM (Anthropic/OpenAI) — extraction
    └→ Graph & verification tasks
```

**Key Data Flow:**
1. User signs up via Supabase Auth
2. Frontend (Vercel) calls FastAPI backend (Fly.io)
3. User creates project with YouTube URL
4. Worker downloads video metadata, triggers domain discovery (LLM)
5. User selects domains → worker ingests audio, transcribes, extracts knowledge
6. Graph built in Neo4j; verification runs cross-video claim scoring
7. Report generation exports graph with citations

## Quick Commands

### Frontend (Next.js + Vercel)

**Local development:**
```bash
cd frontend
npm install
npm run dev              # Start dev server (http://localhost:3000)
npm run build           # Build for production
npm run lint            # Run linting
npm run lint -- --fix   # Fix linting issues
```

**Deployment:**
```bash
# Push to main branch — Vercel auto-deploys
git push origin main

# Deploy to production from current branch (if Vercel CLI installed)
vercel --prod
```

**Preview URLs:**
- Production: https://frontend-3v2bg9a24-cryptohimas-projects.vercel.app
- Staging: varies per branch preview

### Backend (FastAPI + Fly.io)

**Local development (hot-reload, outside Docker):**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload      # http://localhost:8000
# API docs: http://localhost:8000/api/docs
```

**Run tests:**
```bash
cd backend
pytest tests/unit/ -v               # All tests
pytest tests/unit/test_something.py::TestClass::test_method -v  # Single test
pytest -k "test_name" -v            # Filter by pattern
pytest --cov=app --cov-report=html  # With coverage
pytest -x                           # Stop at first failure
pytest --pdb                        # Debug with pdb
```

**Linting & formatting:**
```bash
# No backend linter currently configured
```

**Deployment to Fly.io:**
```bash
# Push changes and trigger Fly deployment
fly deploy

# View logs
fly logs

# SSH into app
fly ssh console
```

### Local Stack Setup

**Start all services (Database, Redis, Neo4j, Celery workers, etc.):**
```bash
cd /Users/root1/agentcraft/youtube-kg
docker compose up -d

# Verify all services are healthy
docker compose ps

# View logs
docker compose logs -f api        # FastAPI
docker compose logs -f worker     # Celery worker
docker compose logs -f beat       # Scheduler (periodic tasks)
docker compose logs -f whisper    # Transcription service
docker compose logs -f frontend   # Next.js dev server (if running in Docker)
```

**Run Next.js frontend locally (outside Docker, for hot-reload):**
```bash
cd frontend
npm install
npm run dev  # Runs on http://localhost:3000
```

**Configure frontend `.env.local` for local backend:**
```
NEXT_PUBLIC_SUPABASE_URL=https://xxxx.supabase.co  # Use test Supabase instance
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-test-anon-key
NEXT_PUBLIC_API_URL=http://localhost:8000          # Points to Docker FastAPI
```

**Run FastAPI backend locally (outside Docker, for hot-reload):**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Access services:**
- Frontend: http://localhost:3000
- FastAPI docs: http://localhost:8000/api/docs (if running standalone) or http://localhost/api/docs (via nginx in Docker)
- Flower (Celery monitor): http://localhost/flower
- MinIO console: http://localhost/minio
- Neo4j browser: http://localhost:7474
- Grafana: http://localhost:3000 (warning: conflicts with frontend dev server; change Next.js to :3001 or use Docker for frontend)

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
frontend/
├── app/                     # Next.js App Router
│   ├── layout.tsx           # Root layout, providers (auth, query client)
│   ├── page.tsx             # Home/landing page
│   ├── auth/                # Auth pages (signup, login, callback)
│   ├── dashboard/           # Dashboard (projects list)
│   ├── projects/            # Project detail, graph visualization
│   └── globals.css          # Tailwind styles
├── lib/                     # Utilities
│   ├── supabase.ts          # Supabase client
│   └── api.ts               # Axios API client helpers
├── components/              # Reusable UI components
├── tailwind.config.ts       # Tailwind configuration
├── tsconfig.json            # TypeScript configuration
├── .env.local               # Local environment (Supabase URL, anon key, API URL)
└── package.json
```

**Stack:** Next.js 16, React 18, TypeScript, Tailwind CSS, Radix UI, TanStack Query (React Query), Supabase Auth, Axios, react-force-graph-2d.

**Key Patterns:**
- App Router pages are server components by default; use `'use client'` for interactive components
- Supabase authentication via `@supabase/auth-helpers-nextjs` and `@supabase/auth-helpers-react`
- API calls via `axios` to FastAPI backend; use React Query for caching and state
- Client state via Zustand or React hooks
- Graph visualization uses `react-force-graph-2d` for rendering knowledge graphs
- Environment variables prefixed `NEXT_PUBLIC_` are exposed to browser (Supabase URL, anon key)
- Backend URL passed via `NEXT_PUBLIC_API_URL` — FastAPI backend on Fly.io

**Supabase Auth Flow:**
1. User signs up/logs in via Supabase UI in `/auth` page
2. Supabase returns JWT token in session
3. Frontend sends JWT in `Authorization: Bearer <token>` header to FastAPI
4. FastAPI verifies JWT using `SUPABASE_JWT_SECRET`
5. Authenticated requests create/fetch projects from FastAPI

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

### Frontend (`.env.local`)
```
NEXT_PUBLIC_SUPABASE_URL=https://xxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
NEXT_PUBLIC_API_URL=http://localhost:8000  # local dev: FastAPI on :8000
                                           # production: https://home.agentcraftconsultancy.com
```

### Backend (`.env`)
See `.env.example` for full list. Critical ones:

**LLM & Services:**
- `YOUTUBE_API_KEY` — YouTube Data API v3 key
- `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` — LLM provider secret
- `LLM_PROVIDER` — "anthropic" (default) or "openai"
- `LLM_MODEL` — e.g., "claude-haiku-4-5-20251001"
- `LLM_REPORT_MODEL` — higher quality model for reports, e.g., "claude-sonnet-4-6"

**Databases (Docker Compose defaults):**
- `DATABASE_URL` — PostgreSQL: `postgresql+asyncpg://youtubekg:changeme@postgres:5432/youtubekg`
- `NEO4J_URI` — `bolt://neo4j:7687`; `NEO4J_USER`, `NEO4J_PASSWORD`
- `REDIS_URL` — `redis://redis:6379/0`
- `QDRANT_HOST=qdrant`, `QDRANT_PORT=6333`
- `MINIO_ENDPOINT=minio:9000`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`

**Supabase Auth:**
- `SUPABASE_JWT_SECRET` — From Supabase project settings > API. Backend uses this to verify Supabase JWTs

**Deployment (Fly.io):**
- `CORS_ORIGINS` — `https://home.agentcraftconsultancy.com` (production) or `http://localhost:3000` (dev)
- `SECRET_KEY` — Random 64-char string for session encryption

**Optional:**
- `DEVICE` — "cpu" or "cuda" (affects Whisper performance; default "cpu")

**Setup:**
1. Copy `.env.example` → `.env`
2. Generate Supabase project at https://supabase.com
3. Set `VITE_SUPABASE_URL` (project URL) and `VITE_SUPABASE_ANON_KEY` (anon key)
4. Copy JWT secret from Supabase to `SUPABASE_JWT_SECRET`
5. Set YouTube API key and LLM secrets
6. Docker Compose reads from `.env` automatically

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

## Deployment Strategy

### Local Development (Docker Compose)
```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f api      # FastAPI
docker compose logs -f worker   # Celery
docker compose logs -f frontend # Next.js

# Bring down
docker compose down
```

**Health Checks:** Configured on API (`/health` endpoint) and PostgreSQL; services restart on unhealthy state.

**Networks:** `public` (nginx on :80) and `internal` (service-to-service communication). PostgreSQL, Neo4j, Redis, Qdrant are internal only.

### Production Deployment

**Frontend (Vercel):**
- Connected to GitHub repo; auto-deploys on push to `main` branch
- Environment variables set in Vercel project dashboard:
  - `NEXT_PUBLIC_SUPABASE_URL`
  - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
  - `NEXT_PUBLIC_API_URL` (production backend URL)
- Preview deployments created for pull requests
- Current production: https://frontend-3v2bg9a24-cryptohimas-projects.vercel.app

**Backend (Fly.io):**
- Deployed via `fly deploy` command (requires Fly CLI)
- Configuration in `fly.toml` (API server) and `fly-workers.toml` (Celery workers)
- Two separate Fly apps:
  - `hello-fly-rosy-cloud-6603` — FastAPI on port 8000/80/443
  - `youtube-kg-workers` — Celery workers (no public ports)
- External services required:
  - **Supabase PostgreSQL** — Database (managed service)
  - **Neo4j** — Knowledge graph (self-hosted or managed)
  - **Qdrant** — Vector store (self-hosted or managed)
  - **Redis** — Message broker (Fly.io Redis or external)
  - **Object storage** — S3-compatible for transcripts/reports
- Environment variables set via `fly secrets` command
- Health checks configured on `/health` endpoint; auto-restart on failure
- Rolling deployment strategy (gradual rollout)

**Cloudflare Tunnel (optional):**
- `cloudflared` container in docker-compose provides secure tunnel
- Maps `agentcraftconsultancy.com` → local `nginx:80`
- For production Fly.io, use Fly's own networking or Cloudflare DNS

### Docker Build Strategy
- **Multi-stage Dockerfile:** dev stage (with dev dependencies) and production stage (minimal runtime)
- Backend build target controlled by compose vs. Fly config
- Frontend: Next.js build in Vercel (no Docker needed for production)

## Authentication Flow

**Supabase Auth (Production):**
1. User visits frontend (Vercel)
2. Frontend redirects to `/auth` page
3. Supabase Auth UI handles signup/login (email/password)
4. On success, Supabase returns JWT session token
5. Frontend stores JWT in browser session via `@supabase/auth-helpers-nextjs`
6. When calling FastAPI, frontend sends: `Authorization: Bearer <token>`
7. FastAPI middleware verifies token using `SUPABASE_JWT_SECRET`
8. Backend extracts user info from JWT claims (`sub` = user_id)

**Local Development (Docker):**
- Same flow; Supabase URL points to local or test instance
- Test credentials in `.env`: `FIRST_SUPERUSER_EMAIL` and `FIRST_SUPERUSER_PASSWORD`

**Token Verification (FastAPI):**
- See `app/core/security.py` — `verify_supabase_token()`
- Tokens verified against `SUPABASE_JWT_SECRET`
- User ID extracted from `sub` claim
- If `SUPABASE_JWT_SECRET` not set, falls back to local JWT (for backward compatibility)

## Frontend-Backend Integration

**API Client Setup (`lib/api.ts`):**
- Axios instance configured with `NEXT_PUBLIC_API_URL` (base URL)
- Default headers include `Authorization: Bearer <jwt_token>` from Supabase session
- Request/response types mirror FastAPI schemas (Pydantic models)

**Making API Calls from Components:**
```typescript
// Example: Create a project
import { useAuth } from '@supabase/auth-helpers-react';
import axios from 'axios';

export function CreateProjectForm() {
  const { user } = useAuth();
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;

  const handleCreate = async (url: string) => {
    try {
      const response = await axios.post(
        `${apiUrl}/api/v1/projects`,
        { youtube_url: url },
        {
          headers: {
            Authorization: `Bearer ${await user?.get_jwt_token()}`
          }
        }
      );
      // Use response.data
    } catch (error) {
      // Handle error
    }
  };
}
```

**CORS Configuration:**
- Backend `CORS_ORIGINS` env var controls which frontend URLs can call the API
- Local: `http://localhost:3000`
- Production: `https://frontend-3v2bg9a24-cryptohimas-projects.vercel.app`
- Set via backend `.env` or Fly secrets

**Debugging API Integration:**
1. Check browser Network tab in DevTools to see actual requests/responses
2. Check FastAPI logs: `docker compose logs -f api` or `fly logs` for production
3. Verify JWT token in browser console: `localStorage.getItem('sb-token')`
4. Test endpoint manually: `curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/projects`

## Common Development Tasks

**Changing database schema (PostgreSQL):**
1. Edit model in `backend/app/models/` (SQLAlchemy)
2. Run `cd backend && alembic revision --autogenerate -m "description"`
3. Review generated migration in `alembic/versions/`
4. Test: `alembic upgrade head` (or `downgrade -1`)

**Adding new Neo4j node type:**
1. Update `graph_service.py` — `ensure_constraints()` method
2. Changes are idempotent; re-run won't break existing data
3. For data migrations, write Cypher scripts in worker tasks or directly via driver

**Adding new API endpoint:**
1. Create schema: `app/schemas/something.py` (Pydantic models)
2. Create service: `app/services/something.py` (business logic)
3. Create router: `app/api/v1/something.py` (HTTP handlers)
4. Include router in `app/main.py`: `app.include_router(something.router, prefix="/api/v1")`

**Adding new Celery task:**
1. Create in `app/workers/tasks/something.py` with `@celery_app.task` decorator
2. Call from API endpoint: `tasks.something.delay(args)`
3. Monitor in Flower: http://localhost/flower

**Testing API integration locally:**
1. Start Docker services: `docker compose up -d`
2. Run backend standalone: `cd backend && uvicorn app.main:app --reload`
3. Run frontend: `cd frontend && npm run dev`
4. Frontend `.env.local` points to `http://localhost:8000`
5. Use Supabase test project for auth testing

## Git & Branching

- Current working branch: `claude/youtube-creator-knowledge-graph-d9a8o1`
- Main branch: `main`
- Deployment: Vercel (auto on main), Fly.io (manual `fly deploy`)
- Recent milestones: Next.js migration, Vercel deployment, Fly.io backend setup, Supabase auth integration
