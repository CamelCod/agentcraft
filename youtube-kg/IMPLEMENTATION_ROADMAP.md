# Implementation Roadmap: Production Setup

## Quick Overview

```
Current State (✅ Live)
├─ FastAPI on Fly.io
├─ Supabase PostgreSQL
└─ Authentication working

Goal (🎯 Production Ready)
├─ Database: Alembic migrations ← Phase 1
├─ Jobs: Redis + Celery workers ← Phase 2
├─ APIs: YouTube integration ← Phase 3
├─ Graph: Neo4j knowledge graph ← Phase 4
├─ Search: Qdrant embeddings ← Phase 5
└─ Transcription: Whisper service ← Phase 6
```

## Phase Timeline

| Phase | Service | Time | Priority | Cost | Difficulty |
|-------|---------|------|----------|------|------------|
| 1 | Alembic Migrations | 10 min | 🔴 Critical | $0 | Easy |
| 2 | Redis + Celery | 20 min | 🟠 High | $10/mo | Medium |
| 3 | YouTube API | 5 min | 🟠 High | $0-25/mo | Easy |
| 4 | Neo4j | 30 min | 🟡 Medium | $49/mo+ | Hard |
| 5 | Qdrant | 30 min | 🟡 Medium | $25/mo+ | Hard |
| 6 | Whisper | 30 min | 🟢 Low | $0-50/mo | Medium |

## What Each Phase Unlocks

```
Phase 1: Migrations ✅
├─ Proper database schema management
├─ Idempotent migrations (safe to re-run)
└─ Foundation for all other features

Phase 2: Redis + Celery ✅
├─ Background job processing
├─ Asynchronous video ingestion
├─ Domain discovery
└─ Knowledge extraction
└─ Claim verification

Phase 3: YouTube API ✅
├─ Video metadata fetching
├─ Creator information
└─ Basic content discovery

Phase 4: Neo4j ✅
├─ Knowledge graph storage
├─ Entity relationships
├─ Cross-video connections
└─ Graph-based queries

Phase 5: Qdrant ✅
├─ Semantic search
├─ Claim similarity matching
├─ Intelligent verification
└─ Recommendation engine

Phase 6: Whisper ✅
└─ Automatic transcription
```

## Dependencies

```
Phase 1 (Migrations)
  ↓ (Everything depends on this)
Phase 2 (Redis + Celery)
  ├→ Phase 3 (YouTube) [independent]
  ├→ Phase 4 (Neo4j) [independent]
  ├→ Phase 5 (Qdrant) [independent]
  └→ Phase 6 (Whisper) [independent]
```

All phases can run in parallel after Phase 1 & 2 complete.

## Cost Breakdown

### Monthly Estimate (Production)

| Service | Free Tier | Pro Tier | Notes |
|---------|-----------|----------|-------|
| Supabase (DB) | ✓ Included | $25+/mo | Already using |
| Fly.io (App) | $5/mo | $10+/mo | 2x shared CPUs |
| Redis on Fly | $0 | $10+/mo | Self-hosted option |
| Neo4j Cloud | ✓ Free | $49+/mo | Managed service |
| Qdrant Cloud | ✓ Free | $25+/mo | Managed service |
| YouTube API | ✓ 10K/day free | $0.25/1K units | ~$50/mo for 1K videos |
| Whisper (OpenAI) | - | $0.006/min | ~$36/mo for 100 hours |
| **Total** | ~$5 | ~$150+/mo | Rough estimate |

## Decision Tree: Self-Hosted vs Managed

### Redis
- **Self-hosted on Fly**: Free (0 data transfer within Fly)
- **Managed**: Not needed, self-hosted is simple
- **Recommendation**: Self-hosted on Fly ✅

### Neo4j
- **Self-hosted on Fly**: 2GB RAM machine ($15/mo) + storage
- **Managed Cloud**: $49+/mo
- **Recommendation**: Managed Cloud (better support, reliability) ✅

### Qdrant
- **Self-hosted on Fly**: 2GB RAM machine + storage
- **Managed Cloud**: $25+/mo
- **Recommendation**: Managed Cloud (easier, better performance) ✅

### Whisper
- **Self-hosted on Fly**: 4GB RAM machine + compute ($50+/mo), slow
- **OpenAI API**: $0.006/min of audio (~$36/mo for heavy use)
- **Recommendation**: OpenAI API (cheaper, faster, reliable) ✅

## Setup Script Template

For each phase, you'll need:

```bash
# 1. Update code (if needed)
# 2. Set environment variables
flyctl secrets set VAR=value --app hello-fly-rosy-cloud-6603

# 3. Deploy
flyctl deploy --app hello-fly-rosy-cloud-6603

# 4. Test
curl https://hello-fly-rosy-cloud-6603.fly.dev/initialization-status | jq .

# 5. Verify logs
flyctl logs --app hello-fly-rosy-cloud-6603 | grep "ERROR\|WARNING"
```

## Graceful Degradation

App works with any subset of services:

```
✅ All services running
  ├─ Full featured application
  └─ Perfect video analysis & knowledge extraction

✅ Only DB + API
  ├─ Can browse projects and settings
  ├─ Cannot: ingest videos, extract knowledge, search
  └─ User sees: "Service unavailable, try again later"

✅ Only DB + API + Redis
  ├─ Can ingest videos asynchronously
  ├─ Cannot: build graph, search
  └─ Shows progress bar in UI

✅ Only DB + API + Neo4j
  ├─ Can store knowledge but cannot compute it
  ├─ Cannot: ingest videos, search embeddings
  └─ Shows: "Graph ready, add content"
```

## Implementation Decision: Which to Do First?

### If you want to test/demo ASAP:
1. ✅ Phase 1: Migrations (critical foundation)
2. ✅ Phase 2: Redis + Celery (enables async)
3. ✅ Phase 3: YouTube API (enables input)
→ Can now ingest videos and process them

### If you want full features:
1. ✅ Phase 1: Migrations
2. ✅ Phase 2: Redis + Celery
3. ✅ Phase 3: YouTube API
4. ✅ Phase 4: Neo4j (knowledge graph)
5. ✅ Phase 5: Qdrant (semantic search)
6. ⏳ Phase 6: Whisper (transcription)

### If you want minimum viable:
1. ✅ Phase 1: Migrations (database only)
→ App keeps working, services optional

## Progress Tracking

```
[ ] Phase 1: Migrations (10 min)
    [ ] Verify Alembic runs on startup
    [ ] Check initialization-status shows migrations: true
    [ ] Test: Create a project (stores in DB)

[ ] Phase 2: Redis + Celery (20 min)
    [ ] Create Redis app on Fly
    [ ] Create Celery worker app on Fly
    [ ] Set connection strings as secrets
    [ ] Test: Background task completes

[ ] Phase 3: YouTube API (5 min)
    [ ] Get API key from Google Cloud
    [ ] Set secret on Fly
    [ ] Test: Create project with YouTube URL

[ ] Phase 4: Neo4j (30 min)
    [ ] Choose managed or self-hosted
    [ ] Create instance
    [ ] Set connection secrets
    [ ] Test: initialization-status shows graph: true

[ ] Phase 5: Qdrant (30 min)
    [ ] Choose managed or self-hosted
    [ ] Create instance
    [ ] Set connection secrets
    [ ] Test: initialization-status shows qdrant: true

[ ] Phase 6: Whisper (30 min)
    [ ] Choose OpenAI or self-hosted
    [ ] Set API key or deploy service
    [ ] Test: Transcription works

[ ] Final: Production Verification
    [ ] All initialization-status checks pass
    [ ] Create full project with all features
    [ ] Verify knowledge graph built
    [ ] Check claim verification works
    [ ] Performance test under load
```

## When You're Ready

Start with **Phase 1** - it's the foundation and lowest risk.

Let me know which phase you want to implement first, and I'll provide:
- ✅ Exact file changes needed
- ✅ Complete commands to run
- ✅ Environment variables to set
- ✅ Testing instructions
- ✅ Rollback steps if something fails

---

**Recommendation**: Start with Phase 1 → 2 → 3 to get a working video ingestion pipeline. Then add 4 & 5 for the knowledge graph features.
