# Production Setup Guide for YouTube Creator Knowledge Graph

## Current Status
- ✅ FastAPI app live on Fly.io
- ✅ Supabase PostgreSQL connected
- ✅ Authentication working (signup/login)
- ⏳ Optional services: Redis, Neo4j, Qdrant, Celery, Whisper

## Implementation Order (Recommended)

This order ensures:
1. Database is properly migrated
2. Job queue is ready for background tasks
3. Knowledge graph and embeddings are available
4. All optional services degrade gracefully if unavailable

### Phase 1: Database Migrations (Foundation)
**Time**: ~10 minutes  
**Risk**: Low (migrations are idempotent)  
**Impact**: Required for advanced features

### Phase 2: Redis + Celery (Background Jobs)
**Time**: ~20 minutes  
**Risk**: Low (app works without Celery)  
**Impact**: Enables async task processing (video ingestion, domain discovery)

### Phase 3: YouTube API Setup
**Time**: ~5 minutes  
**Risk**: None (just configuration)  
**Impact**: Enables video metadata fetching

### Phase 4: Neo4j Setup (Knowledge Graph)
**Time**: ~30 minutes  
**Risk**: Medium (needs external service)  
**Impact**: Core feature - knowledge graph storage

### Phase 5: Qdrant Setup (Vector Search)
**Time**: ~30 minutes  
**Risk**: Medium (needs external service)  
**Impact**: Core feature - semantic search and claim verification

### Phase 6: Whisper Service (Transcription)
**Time**: ~30 minutes  
**Risk**: Medium (resource-intensive)  
**Impact**: Enables video transcription

---

## Phase 1: Database Migrations

### What It Does
Runs Alembic migrations to set up database schema properly. The app currently tries to create tables on startup, but Alembic is the proper way to manage schema changes.

### Current Issue
Previous deployments left partial schema in Supabase. Alembic migration table (`alembic_version`) already exists, causing conflicts.

### Fix

**1. Update the initial migration to handle existing tables:**

```python
# File: backend/alembic/versions/001_initial_schema.py
# Change to:

"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-06-09
"""
from alembic import op
import sqlalchemy as sa

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create extensions if they don't exist
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')
    
    # Only create tables if they don't exist
    # (Alembic will handle this, but be explicit for idempotency)
    pass


def downgrade():
    pass
```

**2. Add a new migration to create actual tables:**

```bash
cd backend
alembic revision --autogenerate -m "Create initial tables"
```

This will auto-detect your SQLAlchemy models and create the migration.

**3. Test locally (optional but recommended):**

```bash
# Make sure you have a test PostgreSQL available
cd backend
DATABASE_URL="postgresql://user:pass@localhost/testdb" alembic upgrade head
```

**4. Run on Fly:**

The app's initialization module already runs migrations via:
```python
async def run_migrations() -> bool:
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd="/app",
        capture_output=True,
        text=True,
        timeout=60,
    )
```

This happens automatically on every app startup in the background.

### Test
```bash
# Check initialization status
curl https://hello-fly-rosy-cloud-6603.fly.dev/initialization-status | jq .

# Should show:
# {
#   "status": "completed",
#   "details": {
#     "migrations": true,  # This should now be true
#     "graph": false,      # Expected - Neo4j not running
#     "qdrant": false,     # Expected - Qdrant not running
#     "superuser": true,
#     "success": true
#   }
# }
```

### Rollback
Alembic can roll back: `alembic downgrade -1`

---

## Phase 2: Redis + Celery Workers

### What It Does
- **Redis**: Message broker for Celery, plus general caching
- **Celery**: Background task queue for heavy operations (video ingestion, domain discovery, verification)

### Why It Matters
Without Celery, long-running operations (downloading video, transcribing audio, running LLM) would block API requests. Celery allows them to run asynchronously.

### Setup Steps

**1. Add Redis to Fly (create a separate Redis app):**

```bash
# Create Redis app
flyctl apps create youtube-kg-redis

# Add Redis machine (minimal)
flyctl machine run redis:7-alpine \
  --app youtube-kg-redis \
  --region lhr \
  --vm-memory 512 \
  --port 6379:6379

# Get Redis internal hostname
flyctl machines list --app youtube-kg-redis
```

Note the Redis machine ID, then get its internal hostname:
```bash
# Internal DNS in Fly: <machine-id>.vm.<app-name>.internal:6379
# Example: abc123xyz.vm.youtube-kg-redis.internal:6379
```

**2. Set Redis connection on main app:**

```bash
flyctl secrets set \
  REDIS_URL="redis://abc123xyz.vm.youtube-kg-redis.internal:6379/0" \
  CELERY_BROKER_URL="redis://abc123xyz.vm.youtube-kg-redis.internal:6379/0" \
  CELERY_RESULT_BACKEND="redis://abc123xyz.vm.youtube-kg-redis.internal:6379/1" \
  --app hello-fly-rosy-cloud-6603
```

**3. Update initialization to handle missing Redis gracefully:**

```python
# File: backend/app/initialization.py
# Already handles this - if Redis isn't available, Celery tasks just won't queue

async def ensure_celery_ready() -> bool:
    """Check if Celery broker is reachable"""
    try:
        from app.workers.celery_app import celery_app
        # Simple ping test
        celery_app.connection().connect()
        logger.info("Celery broker is ready")
        return True
    except Exception as e:
        logger.warning(f"Celery broker unavailable: {e}")
        return False
```

**4. Deploy Celery workers on Fly:**

Create a separate Celery app:

```bash
# Create the worker app
flyctl apps create youtube-kg-workers

# Create fly.toml for workers
cat > workers-fly.toml << 'EOF'
app = "youtube-kg-workers"
primary_region = "lhr"

[build]
  dockerfile = "Dockerfile.worker"

[env]
  APP_ENV = "production"
  CELERY_BROKER_URL = "redis://abc123xyz.vm.youtube-kg-redis.internal:6379/0"
  CELERY_RESULT_BACKEND = "redis://abc123xyz.vm.youtube-kg-redis.internal:6379/1"
  DATABASE_URL = "postgresql://..." # Same as main app
  
[deploy]
  strategy = "rolling"

[[vm]]
  cpu_kind = "shared"
  cpus = 2
  memory_mb = 1024
EOF

# Set secrets for workers
flyctl secrets set \
  DATABASE_URL="postgresql://..." \
  ANTHROPIC_API_KEY="..." \
  YOUTUBE_API_KEY="..." \
  --app youtube-kg-workers
```

**5. Create Dockerfile for workers:**

```dockerfile
# File: Dockerfile.worker
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend .

# Run Celery worker with 4 concurrent processes
CMD ["celery", "-A", "app.workers.celery_app", "worker", \
     "--loglevel=info", \
     "--concurrency=4", \
     "-Q", "default,discovery,ingestion,extraction,verification,reporting"]
```

**6. Deploy workers:**

```bash
flyctl deploy -c workers-fly.toml --app youtube-kg-workers
```

### Test

```bash
# Check if a task can be queued (will fail gracefully if Redis unavailable)
# This requires adding a test endpoint, or check via logs:
flyctl logs --app youtube-kg-workers | grep "worker ready"

# Should see:
# "Ready to accept tasks"
```

### Graceful Degradation
If Redis is unavailable:
- API still works
- Tasks won't queue
- Users see "task queued but processing delayed" message
- App logs warnings about missing broker

### Rollback
```bash
# Keep the apps, just disconnect them
flyctl secrets delete CELERY_BROKER_URL CELERY_RESULT_BACKEND \
  --app hello-fly-rosy-cloud-6603
# App will degrade gracefully
```

---

## Phase 3: YouTube API Setup

### What It Does
Fetches video metadata (title, description, creator info) from YouTube Data API v3.

### Setup Steps

**1. Get YouTube API Key:**

Go to [Google Cloud Console](https://console.cloud.google.com/)
- Click "Create Project"
- Name it "YouTube KG"
- Enable "YouTube Data API v3"
- Create an API key (Credentials → Create Credentials → API Key)
- Copy the key

**2. Set on Fly:**

```bash
flyctl secrets set \
  YOUTUBE_API_KEY="AIzaSy..." \
  --app hello-fly-rosy-cloud-6603
```

**3. Configure quotas (optional but recommended):**

In Google Cloud Console:
- Go to YouTube Data API v3 → Quotas
- Set daily quota limit (e.g., 100K units/day = ~100 videos)

### Test

```bash
# The app checks this when downloading video metadata
# Make a request to create a project with a YouTube URL
curl -X POST https://hello-fly-rosy-cloud-6603.fly.dev/api/v1/projects \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"youtube_url":"https://www.youtube.com/watch?v=dQw4w9WgXcQ","name":"Test"}'
```

### Cost
- Free tier: 10,000 units/day (enough for testing)
- Production: ~$0.25/1000 units beyond free quota

---

## Phase 4: Neo4j Setup

### What It Does
Stores knowledge graph: entities (people, organizations, concepts), relationships, and claims extracted from videos.

### Why It Matters
**Core feature**: Converting video content into structured knowledge.

### Setup Options

#### Option A: Managed Neo4j Cloud (Recommended)

**1. Create account at [neo4j.com/cloud](https://neo4j.com/cloud/)**

**2. Create instance:**
- Click "Create Database"
- Select "Neo4j 5.x"
- Instance size: "Neo4j 5 Small" (~$49/month) or free tier
- Region: EU
- Database name: "youtubekg"

**3. Get connection info:**
- After creation, click "Connect"
- Note the connection string: `neo4j+s://xxx.databases.neo4j.io`
- Username: `neo4j`
- Password: (copy from "Manage" → "Credentials")

**4. Set on Fly:**

```bash
flyctl secrets set \
  NEO4J_URI="neo4j+s://xxx.databases.neo4j.io:7687" \
  NEO4J_USER="neo4j" \
  NEO4J_PASSWORD="..." \
  --app hello-fly-rosy-cloud-6603
```

#### Option B: Self-hosted on Fly (Advanced)

```bash
# Create Neo4j Fly app
flyctl apps create youtube-kg-neo4j

# Run Neo4j container
flyctl machine run neo4j:5-enterprise \
  --app youtube-kg-neo4j \
  --region lhr \
  --vm-memory 2048 \
  --env NEO4J_AUTH="neo4j/changeme"

# Get internal hostname and update secrets
```

### Test

```bash
# Check initialization status
curl https://hello-fly-rosy-cloud-6603.fly.dev/initialization-status | jq '.details.graph'
# Should eventually show: true

# Or check logs
flyctl logs --app hello-fly-rosy-cloud-6603 | grep "Neo4j"
```

### Important Config
The app auto-creates constraints on startup:

```python
# File: backend/app/services/graph_service.py
def ensure_constraints():
    driver = GraphDatabase.driver(...)
    with driver.session() as session:
        # Creates indexes for common queries
        session.run("CREATE INDEX entity_name IF NOT EXISTS FOR (n:Entity) ON (n.name)")
        # ... more constraints
```

### Cost
- Free tier: Yes (for development)
- Production: $49-500+/month depending on usage

---

## Phase 5: Qdrant Setup

### What It Does
Vector database for semantic search. Stores embeddings of claims, used for:
- Finding similar claims across videos
- Deduplication
- Verification (cross-video validation)

### Why It Matters
**Core feature**: Intelligent claim verification across multiple sources.

### Setup Options

#### Option A: Managed Qdrant Cloud (Recommended)

**1. Create account at [cloud.qdrant.io](https://cloud.qdrant.io/)**

**2. Create cluster:**
- Click "Create Cluster"
- Name: "youtubekg"
- Size: "Free" or smallest paid tier
- Region: EU-001

**3. Get API key:**
- After creation, click cluster
- Copy "API Key" and "URL"
- Format: `https://xxx-qdrant.a1.qdrant.io`

**4. Set on Fly:**

```bash
flyctl secrets set \
  QDRANT_URL="https://xxx-qdrant.a1.qdrant.io" \
  QDRANT_API_KEY="ey..." \
  --app hello-fly-rosy-cloud-6603
```

#### Option B: Self-hosted on Fly

```bash
# Create Qdrant Fly app
flyctl apps create youtube-kg-qdrant

# Run Qdrant
flyctl machine run qdrant/qdrant:latest \
  --app youtube-kg-qdrant \
  --region lhr \
  --vm-memory 2048 \
  --port 6333:6333
```

### Update Config

```python
# File: backend/app/config.py
# Update to support API key:

class Settings(BaseSettings):
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""  # New field
```

### Test

```bash
# Check initialization status
curl https://hello-fly-rosy-cloud-6603.fly.dev/initialization-status | jq '.details.qdrant'
# Should eventually show: true

# App auto-creates collections on startup
```

### Cost
- Free tier: Yes (development)
- Production: $25-100+/month

---

## Phase 6: Whisper Service (Transcription)

### What It Does
Converts video audio to text. Required for knowledge extraction.

### Setup Options

#### Option A: OpenAI API (Simplest)

**1. Set OpenAI API key:**

```bash
flyctl secrets set \
  OPENAI_API_KEY="sk-..." \
  --app hello-fly-rosy-cloud-6603
```

**2. Update service:**

```python
# File: backend/app/services/transcription.py
# Update to use OpenAI Whisper API instead of local service

from openai import OpenAI

async def transcribe_with_openai(audio_file_path: str) -> str:
    client = OpenAI(api_key=settings.openai_api_key)
    with open(audio_file_path, "rb") as audio:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio,
        )
    return transcript.text
```

**3. Cost:**
~$0.006 per minute of audio

#### Option B: Self-hosted Whisper Service

```bash
# Create Whisper Fly app
flyctl apps create youtube-kg-whisper

# Run Whisper service
flyctl machine run pytorch/pytorch:2.0-cuda11.8-runtime-ubuntu22.04 \
  --app youtube-kg-whisper \
  --region lhr \
  --vm-memory 4096 \
  # Install Whisper...
```

**Or use existing service:**
- Replicate API (replicate.com) - pay per request
- Hugging Face Inference API

#### Option C: Keep Default (Fly-hosted)

Current config expects Whisper at `http://localhost:9002`. For production:

```bash
# Add Whisper service to docker-compose or separate Fly app
# Keep log warnings about unavailable Whisper - it will be skipped
```

### Test

```bash
# The app will handle missing Whisper gracefully
# Logs will show: "Warning: Could not set up Whisper"
# Domain discovery will still work (uses descriptions instead)
```

---

## Complete Configuration Summary

### Environment Variables Checklist

```bash
# Core (already set)
DATABASE_URL="postgresql://..."
SECRET_KEY="..."
LLM_PROVIDER="anthropic"
ANTHROPIC_API_KEY="..."

# YouTube API
YOUTUBE_API_KEY="AIzaSy..."

# Redis & Celery (Phase 2)
REDIS_URL="redis://..."
CELERY_BROKER_URL="redis://..."
CELERY_RESULT_BACKEND="redis://..."

# Neo4j (Phase 4)
NEO4J_URI="neo4j+s://..."
NEO4J_USER="neo4j"
NEO4J_PASSWORD="..."

# Qdrant (Phase 5)
QDRANT_URL="https://..."
QDRANT_API_KEY="..."

# Whisper (Phase 6 - Optional)
OPENAI_API_KEY="sk-..."  # If using OpenAI
# OR
WHISPER_SERVICE_URL="http://localhost:9002"  # If self-hosted
```

### Set All at Once

```bash
# After completing all phases, set everything:
flyctl secrets set \
  YOUTUBE_API_KEY="..." \
  REDIS_URL="..." \
  CELERY_BROKER_URL="..." \
  CELERY_RESULT_BACKEND="..." \
  NEO4J_URI="..." \
  NEO4J_USER="..." \
  NEO4J_PASSWORD="..." \
  QDRANT_URL="..." \
  QDRANT_API_KEY="..." \
  --app hello-fly-rosy-cloud-6603
```

---

## Monitoring & Health Checks

### Dashboard Endpoints

```bash
# Check which services are ready
curl https://hello-fly-rosy-cloud-6603.fly.dev/initialization-status | jq .

# Expected output after all phases:
{
  "status": "completed",
  "details": {
    "migrations": true,    # Phase 1
    "graph": true,         # Phase 4
    "qdrant": true,        # Phase 5
    "superuser": true,
    "success": true
  }
}
```

### Logs for Each Service

```bash
# Main app
flyctl logs --app hello-fly-rosy-cloud-6603 | grep "ERROR\|WARNING"

# Celery workers
flyctl logs --app youtube-kg-workers | grep "ready\|failed"

# Redis
flyctl logs --app youtube-kg-redis | grep "ERROR"

# Neo4j (if Fly-hosted)
flyctl logs --app youtube-kg-neo4j | grep "ERROR"
```

### Health Check for All Services

```python
# File: backend/app/api/v1/health.py (create this)
from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.get("/detailed-health")
async def detailed_health():
    """Check health of all optional services"""
    status = {
        "api": "ok",
        "database": await check_database(),
        "redis": await check_redis(),
        "neo4j": await check_neo4j(),
        "qdrant": await check_qdrant(),
    }
    
    # API is up if /health endpoint is reachable
    # Other services are optional
    return status
```

---

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Redis down | No background jobs | Log warning, accept requests, skip async tasks |
| Neo4j down | No knowledge graph | Return empty graph, continue with embeddings |
| Qdrant down | No semantic search | Disable verification, continue with other features |
| Whisper down | No transcription | Use video description instead, warn user |
| YouTube API quota | Can't fetch videos | Return error message, suggest retry later |
| Database migration fails | Can't serve requests | Automatic rollback via Alembic |

---

## Implementation Checklist

- [ ] Phase 1: Database migrations (automated, just verify)
- [ ] Phase 2: Redis + Celery workers
- [ ] Phase 3: YouTube API key
- [ ] Phase 4: Neo4j (managed or self-hosted)
- [ ] Phase 5: Qdrant (managed or self-hosted)
- [ ] Phase 6: Whisper (OpenAI or self-hosted)
- [ ] Test: `/initialization-status` shows all true
- [ ] Test: Create project with YouTube URL
- [ ] Test: Verify knowledge graph is built
- [ ] Test: Check background tasks are running
- [ ] Production ready ✅

---

## Quick Reference Commands

```bash
# Deploy main app
flyctl deploy --app hello-fly-rosy-cloud-6603

# Deploy workers (after Phase 2)
flyctl deploy -c workers-fly.toml --app youtube-kg-workers

# Check status
flyctl status --app hello-fly-rosy-cloud-6603
flyctl logs --app hello-fly-rosy-cloud-6603 --no-tail

# Set secrets
flyctl secrets set VAR=value --app hello-fly-rosy-cloud-6603

# Scale machines
flyctl scale count 2 --app hello-fly-rosy-cloud-6603
```

---

## Next Steps

Choose a phase and let's implement it step by step with exact commands and testing instructions for each change.
