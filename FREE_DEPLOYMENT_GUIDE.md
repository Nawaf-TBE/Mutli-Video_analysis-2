# 🆓 FREE Deployment Guide

Deploy your Multi-Video Analysis Platform using **100% FREE** services!

## 🎯 What You'll Get (All FREE)

| Service | Provider | What It Does | Free Tier |
|---------|----------|--------------|-----------|
| **Frontend** | Vercel | Next.js hosting | ✅ Unlimited projects |
| **Backend** | Railway | FastAPI hosting | ✅ $5 monthly credit |
| **Database** | Supabase | PostgreSQL | ✅ 500MB storage |
| **Vector DB** | Qdrant Cloud | Vector search | ✅ 1GB cluster |

**Total Monthly Cost: $0** 🎉

---

## 🚀 Quick Start (5 Minutes)

```bash
# Run the automated deployment script
./deploy_free.sh
```

**Or follow the manual steps below:**

---

## 📋 Manual Deployment Steps

### **1. 🌐 Deploy Frontend (Vercel)**

```bash
cd frontend

# Install Vercel CLI
npm install -g vercel

# Build and deploy
npm run build
vercel --prod

# Follow prompts:
# ✅ Link to existing project? No
# ✅ Project name: multi-video-frontend
# ✅ Deploy? Yes
```

**Result:** Your frontend will be live at `https://your-app.vercel.app`

### **2. 🚀 Deploy Backend (Railway)**

1. **Visit:** https://railway.app
2. **Sign up** with GitHub (free)
3. **New Project** → **Deploy from GitHub repo**
4. **Select** your repository
5. **Configure:**
   - **Root Directory:** `/` (leave empty)
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn src.app.main:app --host 0.0.0.0 --port $PORT`

**Result:** Backend will be live at `https://your-app.railway.app`

### **3. 🗄️ Setup Database (Supabase)**

1. **Visit:** https://supabase.com
2. **New Project** (free account)
3. **Project Details:**
   - Name: `multi-video-db`
   - Password: (generate strong password)
   - Region: (closest to you)
4. **Get Connection String:**
   - Settings → Database → Connection String
   - Copy the PostgreSQL URL

### **4. 🔍 Setup Vector Database (Qdrant Cloud)**

1. **Visit:** https://cloud.qdrant.io
2. **Free Account** signup
3. **Create Cluster:**
   - Name: `video-search`
   - Plan: **Free** (1GB)
   - Region: (closest to you)
4. **Get Cluster URL** from dashboard

### **5. ⚙️ Configure Environment Variables**

In **Railway dashboard** → **Variables**, add:

```bash
DATABASE_URL=postgresql://postgres:[password]@[host]:[port]/postgres
OPENAI_API_KEY=sk-...your-openai-key
QDRANT_URL=https://[cluster-id].cloud.qdrant.io
ENVIRONMENT=production
PORT=8000
```

In **Vercel dashboard** → **Settings** → **Environment Variables**, add:

```bash
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```

---

## 🎯 Free Tier Limits

### **Railway ($5 Monthly Credit)**
- ✅ **1GB** RAM, **1vCPU**
- ✅ **1GB** disk storage  
- ✅ **Unlimited** bandwidth
- ⚠️ Sleeps after 30 min inactivity

### **Vercel (Unlimited)**
- ✅ **Unlimited** projects
- ✅ **100GB** bandwidth/month
- ✅ **100** serverless executions/day

### **Supabase (500MB)**
- ✅ **500MB** database storage
- ✅ **50,000** monthly API requests
- ✅ **2** projects max

### **Qdrant Cloud (1GB)**
- ✅ **1GB** storage
- ✅ **100,000** vectors
- ✅ **Unlimited** searches

---

## 🔧 Optimization for Free Tiers

### **Reduce Memory Usage (Railway)**
```python
# In src/app/main.py
import os

# Optimize for free tier
if os.getenv("ENVIRONMENT") == "production":
    # Reduce worker processes
    workers = 1
    # Limit embeddings cache
    max_cache_size = 100
```

### **Database Optimization (Supabase)**
```sql
-- Keep database under 500MB
-- Regular cleanup of old data
DELETE FROM frames WHERE created_at < NOW() - INTERVAL '30 days';
DELETE FROM chat_messages WHERE created_at < NOW() - INTERVAL '7 days';
```

### **Vector Storage (Qdrant)**
```python
# Limit vector dimensions for free tier
vector_size = 384  # Instead of 1536
batch_size = 50    # Smaller batches
```

---

## 📊 Usage Monitoring

### **Railway Dashboard**
- Monitor CPU/Memory usage
- Track $5 credit consumption
- View deployment logs

### **Supabase Dashboard**  
- Database size monitoring
- API request tracking
- Performance metrics

### **Vercel Analytics**
- Page views and performance
- Build minutes usage
- Bandwidth consumption

---

## 🚨 When You Hit Limits

### **Railway Credit Exceeded ($5)**
**Options:**
1. **Wait** for next month's credit
2. **Upgrade** to paid plan ($5/month)
3. **Switch** to Render.com free tier

### **Supabase Storage Full (500MB)**
**Solutions:**
1. **Clean up** old data regularly
2. **Upgrade** to paid plan ($25/month)
3. **Switch** to Railway PostgreSQL ($5/month)

### **Qdrant Vectors Full (100K)**
**Solutions:**
1. **Delete** old video embeddings
2. **Upgrade** to paid cluster
3. **Use** local Qdrant on Railway

---

## 🔄 Migration Path

### **Phase 1: Free Testing** (Current)
- All free services
- Perfect for MVP testing
- ~1000 video uploads

### **Phase 2: Hybrid ($10-20/month)**
- Keep Vercel (free)
- Upgrade Railway to paid
- Upgrade database storage

### **Phase 3: Production ($50+/month)**
- Professional hosting
- Unlimited scaling
- Enterprise features

---

## 🛠️ Troubleshooting

### **Railway App Sleeping**
```bash
# Keep app awake (add to cron job)
curl https://your-app.railway.app/health
```

### **Database Connection Errors**
```bash
# Test connection
psql "postgresql://user:pass@host:port/db"
```

### **Frontend API Errors**
```bash
# Check environment variables
echo $NEXT_PUBLIC_API_URL

# Test backend health
curl https://your-backend.railway.app/health
```

---

## 🎉 Success Checklist

- [ ] Frontend deployed to Vercel
- [ ] Backend deployed to Railway  
- [ ] Database created on Supabase
- [ ] Vector DB created on Qdrant Cloud
- [ ] Environment variables configured
- [ ] App accessible via public URLs
- [ ] Video upload working
- [ ] Chat functionality working
- [ ] Visual search working

---

## 📞 Support Resources

- **Railway:** [Discord Community](https://discord.gg/railway)
- **Vercel:** [Documentation](https://vercel.com/docs)
- **Supabase:** [Discord Community](https://discord.gg/supabase)
- **Qdrant:** [Documentation](https://qdrant.tech/documentation/)

---

**🎯 Ready to deploy? Run: `./deploy_free.sh`**

*Estimated setup time: 15-30 minutes*
*Total cost: $0/month* 🆓 