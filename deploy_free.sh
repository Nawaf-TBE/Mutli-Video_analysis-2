#!/bin/bash

# 🆓 FREE Deployment Script for Multi-Video Analysis Platform
# This script helps you deploy the entire app using free tiers

set -e

echo "🆓 FREE Multi-Video Analysis Platform Deployment"
echo "================================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🎯 This will deploy your app using FREE services:${NC}"
echo "   • Frontend: Vercel (FREE)"
echo "   • Backend: Railway (FREE $5 credit)"
echo "   • Database: Supabase (FREE)"
echo "   • Vector DB: Qdrant Cloud (FREE)"
echo ""

# Check if user wants to continue
read -p "Continue with free deployment? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# Step 1: Check dependencies
echo -e "${BLUE}📋 Checking dependencies...${NC}"

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

if ! command_exists git; then
    echo -e "${RED}❌ Git is required${NC}"
    exit 1
fi

if ! command_exists node; then
    echo -e "${RED}❌ Node.js is required${NC}"
    exit 1
fi

if ! command_exists npm; then
    echo -e "${RED}❌ npm is required${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All dependencies found${NC}"

# Step 2: Prepare backend for Railway
echo -e "${BLUE}🚀 Preparing backend for Railway...${NC}"

# Add gunicorn to requirements if not present
if ! grep -q "gunicorn" requirements.txt; then
    echo "gunicorn==21.2.0" >> requirements.txt
    echo -e "${GREEN}✅ Added gunicorn to requirements.txt${NC}"
fi

# Step 3: Deploy frontend to Vercel
echo -e "${BLUE}🌐 Deploying frontend to Vercel...${NC}"
cd frontend

# Install Vercel CLI if not present
if ! command_exists vercel; then
    echo -e "${YELLOW}📦 Installing Vercel CLI...${NC}"
    npm install -g vercel
fi

# Build frontend
echo -e "${YELLOW}🔨 Building frontend...${NC}"
npm run build

# Deploy to Vercel
echo -e "${BLUE}🚀 Deploying to Vercel...${NC}"
echo -e "${YELLOW}⚠️  Follow the prompts to login and deploy${NC}"
vercel --prod

cd ..

# Step 4: Instructions for Railway backend
echo ""
echo -e "${GREEN}🎉 Frontend deployed to Vercel!${NC}"
echo ""
echo -e "${BLUE}📋 Next steps for Railway backend:${NC}"
echo "1. Visit: https://railway.app"
echo "2. Sign up with GitHub"
echo "3. Connect this repository"
echo "4. Deploy the backend service"
echo "5. Add environment variables (see below)"
echo ""

# Step 5: Environment variables template
echo -e "${YELLOW}🔧 Required Environment Variables for Railway:${NC}"
cat << 'EOF'

DATABASE_URL=postgresql://user:pass@host:port/database
OPENAI_API_KEY=your_openai_api_key
QDRANT_URL=https://your-cluster.cloud.qdrant.io
ENVIRONMENT=production
PORT=8000

EOF

# Step 6: Database setup instructions
echo -e "${BLUE}🗄️  Database Setup (Supabase):${NC}"
echo "1. Visit: https://supabase.com"
echo "2. Create new project (FREE)"
echo "3. Get PostgreSQL connection string"
echo "4. Use it as DATABASE_URL in Railway"
echo ""

# Step 7: Vector database setup
echo -e "${BLUE}🔍 Vector Database Setup (Qdrant Cloud):${NC}"
echo "1. Visit: https://cloud.qdrant.io"
echo "2. Create free cluster (1GB)"
echo "3. Get cluster URL"
echo "4. Use it as QDRANT_URL in Railway"
echo ""

# Step 8: Final instructions
echo -e "${GREEN}🎯 Final Steps:${NC}"
echo "1. Configure environment variables in Railway"
echo "2. Update frontend API URL to point to Railway backend"
echo "3. Test the deployment"
echo ""

echo -e "${GREEN}💰 Total cost: $0/month${NC}"
echo -e "${YELLOW}⚠️  Usage limits apply to free tiers${NC}"
echo ""

echo -e "${BLUE}📚 Helpful Links:${NC}"
echo "• Railway: https://railway.app"
echo "• Vercel: https://vercel.com"
echo "• Supabase: https://supabase.com"
echo "• Qdrant Cloud: https://cloud.qdrant.io"
echo ""

echo -e "${GREEN}🎉 Deployment script completed!${NC}" 