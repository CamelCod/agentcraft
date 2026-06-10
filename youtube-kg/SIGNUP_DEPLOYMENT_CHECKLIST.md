# Signup Flow Deployment Checklist

## Status: ✅ Code Complete

All frontend and backend signup functionality has been implemented and committed to git.

---

## Files Created/Modified

### ✅ New Files
- `frontend/src/pages/SignupPage.tsx` — Public signup form component
- `signup-test.sh` — Comprehensive validation and testing script

### ✅ Modified Files
- `backend/app/schemas/auth.py` — Added `Field(min_length=8)` password validation
- `frontend/src/pages/LoginPage.tsx` — Added signup link + success message display
- `frontend/src/App.tsx` — Added `/signup` route
- `CLAUDE.md` — Complete codebase documentation
- `DEPLOYMENT_PLAN.md` — Deployment architecture and task breakdown

### ✅ Git Status
- Commit: `8ed41f4`
- Branch: `claude/youtube-creator-knowledge-graph-d9a8o1`
- All changes staged and committed

---

## How to Validate Before Deployment

### Prerequisites
```bash
# Start the full Docker Compose stack (from youtube-kg directory)
docker compose up -d

# Wait for all services to be healthy
docker compose ps  # all should show "healthy" or "running"
```

### Run the Validation Script
```bash
bash signup-test.sh http://localhost
```

**Expected Output:**
```
Starting signup flow validation...
Base URL: http://localhost
Test email: test-1781063134@example.com

✓ PASS: API is healthy
✓ PASS: Registration returns 201
✓ PASS: Response has id field
... (7 more tests)

═══════════════════════════════════════
Test Results:
Passed: 10
Failed: 0
═══════════════════════════════════════
All tests passed!
```

### Manual Browser Test
1. Navigate to `http://localhost/signup` (or your domain)
2. Fill in:
   - Full Name: "Test User" (optional)
   - Email: "newuser@example.com"
   - Password: "SecurePass123"
   - Confirm Password: "SecurePass123"
3. Click "Sign Up"
4. **Expected:** Redirect to `/login` with green success banner: "Account created successfully. Please sign in."
5. Login with the new credentials
6. **Expected:** Redirected to `/projects` dashboard

---

## Deployment to Production

### Option A: Self-Hosted on VPS (Recommended)

**Steps:**
1. Push code to `main` branch (or merge PR)
2. SSH into your VPS/server
3. Pull latest code
4. Run:
   ```bash
   docker compose -f docker-compose.yml up -d
   ```
5. Configure Cloudflare DNS to point `agentcraft.com` to the VPS IP
6. Access at `https://agentcraft.com` (set up SSL via Nginx + Let's Encrypt)

**Notes:**
- The `netlify.toml` at the parent level (`/agentcraft/netlify.toml`) is for a different project
- This full-stack app (FastAPI + React + PostgreSQL + Neo4j) cannot run on Netlify (serverless)
- Docker Compose orchestrates all services locally

### Option B: Cloud Deployment (AWS ECS, GCP Cloud Run, etc.)
- Package the entire docker-compose setup as a Terraform/Helm stack
- Or use AWS ECS task definitions for multi-container orchestration
- Ensure PostgreSQL, Neo4j, Redis are backed by managed services in production

---

## Features Implemented

### Frontend
- ✅ Public signup page at `/signup`
- ✅ Email + password validation (client-side password match)
- ✅ Link from login page: "Don't have an account? Sign up"
- ✅ Success redirect to `/login` with green banner message
- ✅ Error handling with API error messages
- ✅ Full Name optional field

### Backend
- ✅ Password minimum length: 8 characters (enforced at schema level)
- ✅ Duplicate email prevention (409 error if exists)
- ✅ Bcrypt password hashing (via `hash_password()`)
- ✅ New users assigned `analyst` role by default
- ✅ JWT token generation (access + refresh tokens)
- ✅ User creation with timestamps

### Testing
- ✅ 10-point validation script covering:
  1. API health check
  2. User registration (HTTP 201)
  3. Response field validation (id, email, role, is_active)
  4. Default role verification (analyst)
  5. Duplicate email prevention (HTTP 400)
  6. Login with new credentials (HTTP 200)
  7. Authenticated request (GET /auth/me)
  8. Invalid credentials rejection (HTTP 401)
  9. Weak password rejection (HTTP 422)
  10. Summary report

---

## Security Checklist

- ✅ Passwords hashed with bcrypt (never stored plaintext)
- ✅ Minimum 8-character password requirement
- ✅ Email validation via Pydantic `EmailStr`
- ✅ JWT tokens with 60-minute expiry (access) + 30-day refresh
- ✅ No hardcoded secrets in code
- ✅ CORS configured (adjust `CORS_ORIGINS` in `.env` for production domain)
- ⚠️ **TODO:** Rate limiting on `/auth/register` and `/auth/login` (optional but recommended)

---

## Optional Enhancements

If you want to add rate limiting (recommended for production):

```python
# backend/app/api/v1/auth.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/register")
@limiter.limit("5/minute")
async def register(request: Request, body: RegisterRequest, db: DB):
    # ... existing code
```

Or use Redis-based rate limiting (more scalable):
```bash
pip install fastapi-limiter2
```

---

## Rollback Plan

If issues arise after deployment:

1. **Code rollback:**
   ```bash
   git revert HEAD~1  # Revert signup commit
   docker compose build --no-cache  # Rebuild images
   docker compose up -d  # Restart services
   ```

2. **Database rollback:**
   - New users created during the issue can be deleted via admin panel or SQL:
     ```sql
     DELETE FROM users WHERE email LIKE '%test%' AND created_at > '2026-06-10';
     ```

3. **Feature toggle:**
   - Comment out signup route in `App.tsx` and redeploy frontend

---

## Next Steps

1. **Merge to main** (when ready for production)
2. **Deploy to VPS/Cloud**
3. **Test signup at production URL**
4. **Monitor logs** for any auth-related errors
5. **Announce to users** that public signup is available

---

## Questions?

- Signup validation: `bash signup-test.sh http://your-domain.com`
- Check logs: `docker compose logs api` or `docker compose logs worker`
- Database queries: Connect to PostgreSQL via `psql` or admin panel
