# 🚀 DentSignal Deployment Guide

## Architecture Overview

```
Vercel (Free)           → Dashboard + Landing Page (Next.js)
DigitalOcean App Platform → Voice Agent API (FastAPI)
Supabase (Free)         → Database for dashboard
```

**Domain:** dentsignal.me
- `dentsignal.me` → Vercel (landing + dashboard)
- `api.dentsignal.me` → DigitalOcean (backend API)

---

## Part 1: Push to GitHub

### Step 1: Create GitHub Repo
1. Go to https://github.com/new
2. Name: `dentsignal`
3. Don't add README
4. Click Create

### Step 2: Push Your Code
```bash
cd "c:\Users\thely\Downloads\Ai voice agent"

# Initialize git (if not already)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - DentSignal voice agent"

# Add remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/dentsignal.git

# Push
git push -u origin main
```

---

## Part 2: Deploy Dashboard to Vercel (Free)

### Step 1: Connect to Vercel
1. Go to https://vercel.com
2. Sign in with GitHub
3. Click "Import Project"
4. Select `dentsignal` repo
5. **Root Directory:** `dashboard`
6. Framework: Next.js (auto-detected)

### Step 2: Environment Variables
Add these in Vercel dashboard → Settings → Environment Variables:

```
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
NEXT_PUBLIC_API_URL=https://api.dentsignal.me
```

### Step 3: Custom Domain
1. Vercel → Project → Settings → Domains
2. Add: `dentsignal.me`
3. Add: `www.dentsignal.me`
4. Follow DNS instructions (add to Namecheap)

---

## Part 3: Deploy Backend to DigitalOcean App Platform

### Step 1: Create App
1. Go to https://cloud.digitalocean.com/apps
2. Click "Create App"
3. Source: GitHub → Select `dentsignal` repo
4. **Source Directory:** `/dental_agent`
5. Type: Web Service
6. Plan: Basic ($5/mo)

### Step 2: Configure Build
- Build Command: `pip install -r requirements.txt`
- Run Command: `uvicorn api_main:app --host 0.0.0.0 --port 8080`
- HTTP Port: 8080

### Step 3: Environment Variables
Add in App Platform → Settings → App-Level Environment Variables:

```
DATABASE_URL=postgresql://... (use Supabase connection string)
JWT_SECRET=generate_64_char_hex
API_BASE_URL=https://api.dentsignal.me
WS_BASE_URL=wss://api.dentsignal.me
TELEPHONY_MODE=TWILIO
TWILIO_ACCOUNT_SID=ACxxxxx
TWILIO_AUTH_TOKEN=xxxxx
TWILIO_PHONE_NUMBER=+1xxxxxxxxxx
DEEPGRAM_API_KEY=xxxxx
OPENAI_API_KEY=sk-xxxxx
```

### Step 4: Custom Domain
1. App Platform → Settings → Domains
2. Add: `api.dentsignal.me`
3. Follow DNS instructions

---

## Part 4: Configure DNS (Namecheap)

In Namecheap → Domain List → dentsignal.me → Advanced DNS:

| Type | Host | Value | TTL |
|------|------|-------|-----|
| CNAME | @ | cname.vercel-dns.com | Auto |
| CNAME | www | cname.vercel-dns.com | Auto |
| CNAME | api | YOUR_DO_APP.ondigitalocean.app | Auto |

(Vercel and DigitalOcean will give you the exact CNAME values)

---

## Part 5: Configure Twilio Webhooks

In Twilio Console → Phone Numbers → Your Number:

**Voice & Fax → A Call Comes In:**
- Webhook URL: `https://api.dentsignal.me/inbound/voice`
- HTTP POST

---

## Cost Summary

| Service | Monthly Cost |
|---------|-------------|
| Vercel (dashboard) | $0 (free tier) |
| DigitalOcean App Platform | $5-12 |
| Supabase (database) | $0 (free tier) |
| Domain (Namecheap) | $0 (1 year free) |
| **Total** | **$5-12/month** |

With $200 DigitalOcean credits = **16-40 months free**

---

## Testing

```bash
# Health check
curl https://api.dentsignal.me/health

# Visit landing page
open https://dentsignal.me

# Test call
Call your Twilio number!
```

---

## Troubleshooting

### App Platform Build Fails
- Check that `requirements.txt` is in `dental_agent/` folder
- Ensure Python version is specified in runtime.txt if needed

### WebSocket Connection Issues
- App Platform supports WebSockets by default
- Make sure Twilio webhook points to correct URL

### Database Connection
- Use Supabase connection string (already have it)
- Or add DigitalOcean Managed PostgreSQL ($15/mo)

---

## Alternative: Docker Deployment (If App Platform Doesn't Work)

If App Platform has issues with WebSockets or you need more control,
use a Droplet instead. See `docker-compose.yml` in the repo.

