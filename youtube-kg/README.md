# YouTube Creator Knowledge Graph Platform

Self-hosted SaaS that converts a YouTube creator URL into a verified knowledge graph and citation-backed reports.

## Quick Start

```bash
cd youtube-kg
cp .env.example .env
# Edit .env — set YOUTUBE_API_KEY, ANTHROPIC_API_KEY (or OPENAI_API_KEY), all passwords
docker compose up -d
```

Open http://localhost — login with credentials from `.env` (`FIRST_SUPERUSER_EMAIL` / `FIRST_SUPERUSER_PASSWORD`).

## Architecture

```
Browser → Nginx (:80)
             ├── /api/*    → FastAPI (:8000)
             ├── /         → React dashboard (:3000)
             ├── /flower   → Celery monitor (:5555)
             └── /minio    → MinIO console (:9001)

FastAPI → PostgreSQL (state) + Neo4j (graph) + Qdrant (vectors) + Redis (queue)
Celery Worker → yt-dlp (download) → Whisper (transcribe) → LLM (extract) → Neo4j (graph)
```

## Workflow

1. Create project → paste YouTube channel URL
2. Wait ~30s for **domain discovery** (LLM clusters video metadata)
3. **Select domains** you want to analyze
4. System ingests audio, transcribes, extracts knowledge, builds graph (~minutes/hour of content)
5. **Run verification** → cross-video claim scoring
6. **Build report** → download PDF/HTML/Markdown/DOCX/JSON with inline citations

## Services

| Container | Purpose | Port |
|-----------|---------|------|
| `nginx` | Reverse proxy | 80 |
| `api` | FastAPI backend | 8000 (internal) |
| `worker` | Celery task runner | — |
| `beat` | Scheduled tasks | — |
| `flower` | Celery monitor | 5555 (via /flower) |
| `whisper` | Transcription | 9002 (internal) |
| `postgres` | Relational state | 5432 (internal) |
| `neo4j` | Knowledge graph | 7474/7687 (internal) |
| `qdrant` | Vector embeddings | 6333 (internal) |
| `redis` | Task broker | 6379 (internal) |
| `minio` | Object storage | 9000/9001 (internal) |
| `prometheus` | Metrics | 9090 (internal) |
| `grafana` | Dashboards | 3000 (internal) |

## Environment Variables

See `.env.example` for all required variables. Minimum required:
- `YOUTUBE_API_KEY` — YouTube Data API v3 key
- `ANTHROPIC_API_KEY` — for domain discovery and extraction (or set `LLM_PROVIDER=openai` + `OPENAI_API_KEY`)
- All `*_PASSWORD` variables — change from defaults

## Hardware Requirements

- CPU-only: 8 cores, 32GB RAM, 200GB SSD (Whisper will be slow)
- GPU: 8 cores, 32GB RAM, 200GB SSD, NVIDIA GPU ≥8GB VRAM (enable `DEVICE=cuda` in `.env`)

## Development

```bash
# Backend hot-reload (outside Docker)
cd backend && uvicorn app.main:app --reload

# Frontend dev server
cd frontend && npm install && npm run dev

# Run unit tests
cd backend && pytest tests/unit/ -v
```
