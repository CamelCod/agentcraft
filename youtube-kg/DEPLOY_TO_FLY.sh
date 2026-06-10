#!/usr/bin/env bash
# Deploy YouTube KG to Fly.io with full setup
# Run this script to automate the entire deployment process

set -e

echo "════════════════════════════════════════════════════════════════"
echo "YouTube Creator Knowledge Graph - Fly.io Deployment Setup"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 1. Set up PATH for flyctl
export PATH="/Users/root1/.fly/bin:$PATH"

# 2. Get API Token from environment or user input
if [ -z "$FLY_API_TOKEN" ]; then
  echo -e "${YELLOW}Enter your Fly.io API Token:${NC}"
  read -s FLY_API_TOKEN
  echo ""
fi
export FLY_API_TOKEN="$FLY_API_TOKEN"

# 3. Verify flyctl installation
echo -e "${BLUE}1. Verifying Fly.io CLI...${NC}"
if ! command -v /Users/root1/.fly/bin/flyctl &> /dev/null; then
  echo -e "${YELLOW}Installing flyctl...${NC}"
  curl -L https://fly.io/install.sh | sh
fi
echo -e "${GREEN}✓ flyctl ready${NC}"
echo ""

# 4. Authenticate
echo -e "${BLUE}2. Authenticating with Fly.io...${NC}"
/Users/root1/.fly/bin/flyctl auth whoami
echo -e "${GREEN}✓ Authenticated${NC}"
echo ""

# 5. Get API Keys
echo -e "${BLUE}3. Collecting API Keys...${NC}"
echo -e "${YELLOW}Enter ANTHROPIC_API_KEY:${NC}"
read -s ANTHROPIC_API_KEY
echo ""

echo -e "${YELLOW}Enter YOUTUBE_API_KEY:${NC}"
read -s YOUTUBE_API_KEY
echo ""

echo -e "${YELLOW}Enter GOOGLE_API_KEY (optional):${NC}"
read -s GOOGLE_API_KEY
echo ""

echo -e "${GREEN}✓ API keys collected${NC}"
echo ""

# 6. Create PostgreSQL instance
echo -e "${BLUE}4. Creating PostgreSQL instance on Fly...${NC}"
DB_NAME="youtube-kg-db-$(date +%s | tail -c 5)"
echo "App name: $DB_NAME"

/Users/root1/.fly/bin/flyctl postgres create "$DB_NAME" \
  --initial-cluster-size 1 \
  --region lhr \
  --password "$(openssl rand -base64 32)" || true

echo -e "${GREEN}✓ PostgreSQL instance created (or already exists)${NC}"
echo ""

# 7. Create Redis instance
echo -e "${BLUE}5. Creating Redis instance on Fly...${NC}"
REDIS_NAME="youtube-kg-redis-$(date +%s | tail -c 5)"
echo "App name: $REDIS_NAME"

/Users/root1/.fly/bin/flyctl redis create "$REDIS_NAME" \
  --region lhr || true

echo -e "${GREEN}✓ Redis instance created (or already exists)${NC}"
echo ""

# 8. Get Neo4j credentials
echo -e "${BLUE}6. Neo4j Setup (Auradb)...${NC}"
echo -e "${YELLOW}Enter Neo4j URI (from Auradb):${NC}"
echo "Example: neo4j+s://xxxxxxxx.databases.neo4j.io"
read NEO4J_URI
echo ""

echo -e "${YELLOW}Enter Neo4j Username (default: neo4j):${NC}"
read NEO4J_USER
NEO4J_USER=${NEO4J_USER:-neo4j}
echo ""

echo -e "${YELLOW}Enter Neo4j Password:${NC}"
read -s NEO4J_PASSWORD
echo ""

echo -e "${GREEN}✓ Neo4j credentials collected${NC}"
echo ""

# 9. Create .env.fly file
echo -e "${BLUE}7. Creating .env.fly configuration...${NC}"

cat > ".env.fly" << EOF
# Fly.io Production Environment Variables
APP_ENV=production
SECRET_KEY=$(openssl rand -base64 32)
FIRST_SUPERUSER_EMAIL=admin@agentcraftconsultancy.com
FIRST_SUPERUSER_PASSWORD=$(openssl rand -base64 16)

# PostgreSQL (get URL from: flyctl postgres attach)
DATABASE_URL=postgresql://username:password@youtube-kg-db.internal/youtubekg
NEO4J_URI=$NEO4J_URI
NEO4J_USER=$NEO4J_USER
NEO4J_PASSWORD=$NEO4J_PASSWORD

# Redis (get URL from: flyctl redis attach)
REDIS_URL=redis://username:password@youtube-kg-redis.internal:6379

# API Keys
ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY
YOUTUBE_API_KEY=$YOUTUBE_API_KEY
OPENAI_API_KEY=

# LLM Configuration
LLM_PROVIDER=anthropic
LLM_MODEL=claude-haiku-4-5-20251001
LLM_REPORT_MODEL=claude-sonnet-4-6
EMBEDDING_PROVIDER=sentence-transformers

# Whisper (Transcription)
WHISPER_SERVICE_URL=http://whisper:9002
WHISPER_MODEL=medium

# CORS & Domain
CORS_ORIGINS=https://agentcraftconsultancy.com,https://www.agentcraftconsultancy.com
VITE_API_BASE_URL=https://api.agentcraftconsultancy.com

# MinIO (Object Storage)
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=$(openssl rand -base64 16)
MINIO_SECRET_KEY=$(openssl rand -base64 32)
MINIO_SECURE=false

# Celery
CELERY_CONCURRENCY=2
EOF

echo -e "${GREEN}✓ Configuration file created: .env.fly${NC}"
echo ""

# 10. Create Fly secrets
echo -e "${BLUE}8. Setting Fly.io secrets...${NC}"
/Users/root1/.fly/bin/flyctl secrets set \
  ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
  YOUTUBE_API_KEY="$YOUTUBE_API_KEY" \
  NEO4J_URI="$NEO4J_URI" \
  NEO4J_PASSWORD="$NEO4J_PASSWORD" \
  GOOGLE_API_KEY="$GOOGLE_API_KEY"

echo -e "${GREEN}✓ Secrets configured${NC}"
echo ""

# 11. Summary
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Next Steps:"
echo "1. Review .env.fly - update DATABASE_URL and REDIS_URL"
echo "2. Attach databases:"
echo "   flyctl postgres attach youtube-kg-db --app youtube-kg-saas"
echo "   flyctl redis attach youtube-kg-redis --app youtube-kg-saas"
echo "3. Deploy:"
echo "   flyctl deploy --region lhr"
echo "4. Configure DNS in Cloudflare:"
echo "   Point agentcraftconsultancy.com to your Fly app"
echo ""
echo -e "${YELLOW}Save these for reference:${NC}"
echo "PostgreSQL App: $DB_NAME"
echo "Redis App: $REDIS_NAME"
echo ""
