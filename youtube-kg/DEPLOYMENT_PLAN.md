# Deployment Execution Plan & Tool Inventory

## 🔧 Complete Tool Inventory (Loaded & Ready)

### Core Build Tools
| Tool | Purpose | Status |
|------|---------|--------|
| **Read** | Read existing source files | ✅ Loaded |
| **Write** | Create new files (SignupPage.tsx, scripts) | ✅ Loaded |
| **Edit** | Modify existing files (LoginPage, App.tsx, routes) | ✅ Loaded |
| **Bash** | Execute shell commands, git ops, testing | ✅ Loaded |

### Deployment & Infrastructure Tools
| Tool | Purpose | Status |
|------|---------|--------|
| **mcp__supabase__list_tables** | Query Supabase schema | ✅ Loaded |
| **mcp__supabase__execute_sql** | Run SQL queries (validation) | ✅ Loaded |
| **mcp__supabase__list_migrations** | Check database migrations | ✅ Loaded |

### Browser Automation & Testing Tools
| Tool | Purpose | Status |
|------|---------|--------|
| **mcp__claude-in-chrome__tabs_context_mcp** | Get browser tab context | ✅ Loaded |
| **mcp__claude-in-chrome__navigate** | Navigate to URLs | ✅ Loaded |
| **mcp__claude-in-chrome__form_input** | Fill form fields | ✅ Loaded |
| **mcp__claude-in-chrome__read_page** | Read page content & validate | ✅ Loaded |

### Task Management Tools
| Tool | Purpose | Status |
|------|---------|--------|
| **TaskCreate** | Create tasks with dependencies | ✅ Loaded |
| **TaskUpdate** | Mark tasks complete, set blockers | ✅ Loaded |
| **TaskList** | View progress | ✅ Loaded |

---

## 📋 Execution Sequence (Tasks 1-8)

```
Task #5: Verify backend endpoint (parallel, no deps)
    ↓
Task #1: Create SignupPage.tsx
    ├→ Task #2: Add signup link to LoginPage
    │    ↓
    │  Task #3: Update App.tsx routing
    │    ↓
    │  Task #4: Create API client (parallel after #1)
    │
Task #6: Create validation script (depends on #5)
    ↓
Task #7: Push to git (depends on #1-4, #6)
    ↓
Task #8: Run final validation & deploy (depends on #7)
```

---

## 🚀 Build Output Files

### Files to be CREATED:
1. `frontend/src/pages/SignupPage.tsx` — New signup form component
2. `signup-test.sh` — Comprehensive validation & testing script

### Files to be MODIFIED:
1. `frontend/src/pages/LoginPage.tsx` — Add signup link
2. `frontend/src/App.tsx` — Add signup route
3. `frontend/src/api/client.ts` — Add register() function

### Files ALREADY READY:
- ✅ `CLAUDE.md` (created)
- ✅ `backend/app/api/v1/auth.py` (register endpoint exists)
- ✅ `netlify.toml` (deployment config exists)

---

## 📊 Validation Checkpoints

### Checkpoint 1: Backend (Task #5)
```bash
# Verify register endpoint is working
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!","full_name":"Test User"}'

# Expected: 201 + user response with id, email, role
```

### Checkpoint 2: Frontend Build (Task #3)
```bash
# Verify TypeScript compile
cd frontend && npm run build

# Expected: No errors, dist/ folder created
```

### Checkpoint 3: Signup Flow (Task #8)
- Browser test: Navigate to `/signup`
- Fill form: email, password, full_name
- Submit
- Expected: Redirect to `/login` with success message
- Login with new credentials
- Expected: Access to `/projects` dashboard

### Checkpoint 4: Database (Task #8)
```bash
# Verify user created in PostgreSQL
SELECT * FROM user WHERE email = 'newuser@example.com';

# Expected: 1 row with correct hashed password
```

---

## 🔐 Security Checks

- ✅ Passwords hashed with bcrypt (backend handles)
- ✅ JWT tokens with 3600s expiry
- ✅ CORS configured in FastAPI
- ✅ Email validation via Pydantic EmailStr
- ✅ No hardcoded secrets in code

---

## ✅ Final Validation Script (signup-test.sh)

Will test:
1. **API Endpoint** — POST /api/v1/auth/register returns 201
2. **Database** — User inserted in PostgreSQL
3. **Password Hash** — Stored password is bcrypt hashed (not plaintext)
4. **Login Flow** — New user can login with credentials
5. **Tokens** — JWT tokens generated correctly
6. **Frontend** — Signup page loads and submits correctly
7. **Deployment** — Netlify build completes successfully
8. **Domain** — agentcraft.com points to deployed site

---

## 📈 Success Criteria

- [ ] SignupPage.tsx created & renders
- [ ] LoginPage has "Sign up" link
- [ ] App.tsx routes include /signup
- [ ] POST /api/v1/auth/register works
- [ ] User data saved in PostgreSQL
- [ ] Passwords hashed with bcrypt
- [ ] Signup flow end-to-end tested in browser
- [ ] Git changes pushed to main
- [ ] Netlify build triggered & succeeds
- [ ] agentcraft.com/signup loads from deployment
- [ ] New clients can create accounts
- [ ] New clients can login
- [ ] validation script passes all checks

---

## ⏱️ Estimated Time Per Task

| Task | Time | Notes |
|------|------|-------|
| #1 SignupPage | 8 min | Copy LoginPage structure, modify for register |
| #2 LoginPage link | 2 min | Add "Sign up" button/link |
| #3 App.tsx route | 1 min | Add &lt;Route&gt; entry |
| #4 API client | 3 min | Add register() function |
| #5 Backend test | 3 min | curl test |
| #6 Validation script | 10 min | Comprehensive testing script |
| #7 Git push | 2 min | Commit & push |
| #8 Final validation | 5 min | Run script, browser test |

**Total: ~34 minutes** (sequential with some parallelization)

---

## 🎯 Ready to Execute?

All tools are loaded. Task dependencies are set up. 

**Next step:** User says "START BUILD" → Execute Task #1 → Continue through task chain → Run final validation script → Deploy to Netlify → Live signup at agentcraft.com/signup
