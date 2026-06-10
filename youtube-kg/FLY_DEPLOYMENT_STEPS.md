# Fly.io Deployment - Step by Step

## Prerequisites
- ✅ Fly.io account (free tier)
- ✅ Anthropic API key
- ✅ YouTube API key
- ✅ Google credentials (optional)
- ✅ AuraDB Neo4j free account

---

## Quick Start (Automated)

```bash
cd /Users/root1/agentcraft/youtube-kg
bash DEPLOY_TO_FLY.sh
```

The script will:
1. ✅ Authenticate with Fly.io
2. ✅ Create PostgreSQL instance
3. ✅ Create Redis instance
4. ✅ Collect Neo4j credentials
5. ✅ Generate .env.fly file
6. ✅ Set production secrets

---

## Manual Steps (If Script Fails)

### Step 1: Set Up Path & Token
```bash
export PATH="/Users/root1/.fly/bin:$PATH"
export FLY_API_TOKEN="FlyV1 fm2_lJPECAAAAAAAEaT1xBBZPbnyuagcm1sXIx5UGU+3wrVodHRwczovL2FwaS5mbHkuaW8vdjGUAJLOABaezB8Lk7lodHRwczovL2FwaS5mbHkuaW8vYWFhL3YxxDzE5f1x/WIGc8K2rVeort9/ui2bV5g8A9eZ4GZoiNU9rkEkkQr5NgdTKffDkiafP2UoulyGaUkgg7/kTv/ETngyY8yCf/Hyt9V9YosXxxfGrUNQLz/5tM6dpx3TNSWfvcGykmrAqsiDfYME6d5HQR5kHP2QjvmgywFjN9KZwjoUqmUeSpqX4FBiJWRT4sQgCJHig5lHUgC+54BcJCCGDgAQT431CBaqN6FvA8IXWWg=,fm2_lJPETngyY8yCf/Hyt9V9YosXxxfGrUNQLz/5tM6dpx3TNSWfvcGykmrAqsiDfYME6d5HQR5kHP2QjvmgywFjN9KZwjoUqmUeSpqX4FBiJWRT4sQQtYJBkf/4AYzfPVY2V+bKD8O5aHR0cHM6Ly9hcGkuZmx5LmlvL2FhYS92MZgEks5qKOPuzwAAAAEmIQIMF84AFbPsCpHOABWz7AzEEFHSt4F1+JHHQtdgUNiCsqrEILVcBXQ03wunkkBni20EU1stxj3UM98v3YgjseWx0b5B"

/Users/root1/.fly/bin/flyctl auth whoami
```

### Step 2: Create PostgreSQL
```bash
/Users/root1/.fly/bin/flyctl postgres create youtube-kg-db \
  --initial-cluster-size 1 \
  --region lhr
```

Save the connection string!

### Step 3: Create Redis
```bash
/Users/root1/.fly/bin/flyctl redis create youtube-kg-redis \
  --region lhr
```

Save the connection string!

### Step 4: Set Up Neo4j on AuraDB
1. Go to https://neo4j.com/cloud/auradb/
2. Sign up (free)
3. Create instance
4. Get: Neo4j URI, username, password

### Step 5: Configure Secrets
```bash
/Users/root1/.fly/bin/flyctl secrets set \
  ANTHROPIC_API_KEY="your-key-here" \
  YOUTUBE_API_KEY="your-key-here" \
  NEO4J_URI="neo4j+s://xxxxx.databases.neo4j.io" \
  NEO4J_PASSWORD="your-neo4j-password"
```

### Step 6: Attach Databases
```bash
/Users/root1/.fly/bin/flyctl postgres attach youtube-kg-db \
  --app youtube-kg-saas

/Users/root1/.fly/bin/flyctl redis attach youtube-kg-redis \
  --app youtube-kg-saas
```

### Step 7: Deploy
```bash
/Users/root1/.fly/bin/flyctl deploy --region lhr
```

### Step 8: Configure DNS
In Cloudflare:
- Point `agentcraftconsultancy.com` to your Fly app
- Use Fly's provided DNS/IP

---

## Verify Deployment

```bash
# Check app status
/Users/root1/.fly/bin/flyctl status

# View logs
/Users/root1/.fly/bin/flyctl logs

# Test signup
curl https://agentcraftconsultancy.com/api/v1/auth/register \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestPass123"}'
```

---

## Troubleshooting

### Database Connection Failed
- Check credentials in secrets: `flyctl secrets list`
- Verify databases are attached: `flyctl volumes list`

### Domain Not Working
- Wait 5-10 minutes for DNS propagation
- Check Cloudflare DNS settings
- Verify Fly app is deployed: `flyctl status`

### High Memory Usage
- Check scale: `flyctl scale list`
- Reduce Celery workers in fly.toml

---

## Costs

Free tier includes:
- 3 shared-cpu-1x 256MB VMs
- 1 PostgreSQL database (3 shared database hosts)
- 1 Redis database (3 shared redis hosts)

**Expected monthly cost: $5-15** (shared VM overages if needed)

---

## Support

- Fly.io docs: https://fly.io/docs/
- YouTube KG docs: See BUILD_COMPLETE.md
- API docs: https://agentcraftconsultancy.com/api/docs

