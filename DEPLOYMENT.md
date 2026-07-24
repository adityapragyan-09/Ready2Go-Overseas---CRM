# Ready2Go CRM — Production Deployment Guide

## Overview

This guide covers production deployment of the Ready2Go CRM on **Render** with a **GoDaddy custom domain**.

## Architecture

```
Browser → GoDaddy Domain → Render (CDN/SSL)
                                ├── Frontend (React static site)
                                └── Backend (FastAPI + Gunicorn)
                                        ├── Supabase PostgreSQL
                                        └── Supabase Storage
```

## Prerequisites

- **Render account** (render.com)
- **GoDaddy domain** (e.g., crm.ready2gooverseas.com)
- **Supabase project** with Storage bucket `ready2go-documents`
- **GitHub repository** connected to Render

---

## Environment Variables

### Backend (Render Web Service)

| Variable | Value | Notes |
|---|---|---|
| `APP_NAME` | `Ready2Go CRM` | |
| `ENVIRONMENT` | `production` | Required for Supabase mode |
| `DEBUG` | `false` | |
| `API_PREFIX` | `/api/v1` | |
| `SECRET_KEY` | `<random-string>` | Generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `JWT_SECRET_KEY` | `<random-string>` | Same method as SECRET_KEY |
| `JWT_ALGORITHM` | `HS256` | |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | |
| `DATABASE_URL` | `postgresql://user:pass@host:5432/postgres` | Supabase PostgreSQL connection string |
| `FRONTEND_URL` | `https://your-domain.com` | CORS origin |
| `SUPABASE_URL` | `https://your-project.supabase.co` | |
| `SUPABASE_KEY` | `eyJhbGci...` | Supabase service_role key (NOT anon key) |
| `SUPABASE_BUCKET` | `ready2go-documents` | |
| `UPLOAD_DIR` | `uploads` | |
| `MAX_UPLOAD_SIZE_MB` | `500` | |
| `UPLOAD_TIMEOUT_SECONDS` | `600` | |
| `ALLOWED_DOCUMENT_TYPES` | `pdf,jpg,jpeg,png,doc,docx` | |

### Frontend (Render Static Site)

| Variable | Value |
|---|---|
| `VITE_API_BASE_URL` | `https://api.your-domain.com/api/v1` |
| `VITE_API_URL` | `https://api.your-domain.com` |

---

## GoDaddy DNS Configuration

### DNS Records to Add

| Type | Name | Value | TTL |
|---|---|---|---|
| **CNAME** | `www` | `your-frontend.onrender.com` | 600 |
| **CNAME** | `@` | `your-frontend.onrender.com` | 600 |
| **CNAME** | `api` | `your-backend.onrender.com` | 600 |

### Steps

1. Log in to **GoDaddy DNS Manager**
2. Navigate to your domain → **DNS Records**
3. Add the CNAME records above
4. Wait for DNS propagation (10 minutes - 48 hours)

### SSL/HTTPS

Render automatically provisions SSL certificates for custom domains:
- Go to your Render dashboard → your service → **Settings** → **Custom Domain**
- Add your domain (e.g., `crm.ready2gooverseas.com`)
- Render will verify ownership via DNS TXT record
- SSL certificate is auto-provisioned via Let's Encrypt

---

## Render Deployment

### Backend (Web Service)

1. **New Web Service** → Connect your GitHub repo
2. **Settings:**
   - **Name:** `ready2go-crm-api`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r backend/requirements.txt`
   - **Start Command:** `cd backend && gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --timeout 120 --max-requests 10000`
   - **Health Check Path:** `/health`
3. **Environment Variables:** Add all backend variables above
4. **Advanced:**
   - **Auto-Deploy:** Yes (or manual)
   - **Branch:** `main`

### Frontend (Static Site)

1. **New Static Site** → Connect your GitHub repo
2. **Settings:**
   - **Name:** `ready2go-crm-frontend`
   - **Build Command:** `cd frontend && npm install && npm run build`
   - **Publish Directory:** `frontend/dist`
3. **Environment Variables:** Add `VITE_API_BASE_URL` and `VITE_API_URL`
4. **Redirect/Rewrite Rules:**
   - Add a rewrite rule: `/* → /index.html` (for SPA routing)

---

## Pre-Deployment Checklist

### 1. Production Data Reset

```bash
# SSH into a temporary environment or run locally with production DB URL
cd backend
python -m scripts.reset_production
```

This will:
- Delete all employees (except admin)
- Delete all applicants, leads, notifications, documents
- Reset all database sequences
- Attempt to clean Supabase Storage

### 2. Storage Verification

```bash
# Verify storage is clean via API
curl https://your-api.com/api/v1/documents/applicant/1
# Should return empty array
```

### 3. Sequence Verification

```bash
# After reset, create a test applicant and verify it gets APP-000001
```

### 4. Run Migration

```bash
python -m scripts.migrate_document_storage
```

---

## Post-Deployment Verification

### Endpoints to Verify

```bash
# Health
curl https://your-api.com/health
# → {"status": "healthy"}

# Ready
curl https://your-api.com/ready
# → {"status": "ready", "database": "connected"}

# Version
curl https://your-api.com/version
# → {"app": "Ready2Go CRM", "environment": "production"}

# Admin Login
curl -X POST https://your-api.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "your-password"}'
# → {"success": true, "data": {"access_token": "..."}}

# Dashboard (authenticated)
curl https://your-api.com/api/v1/dashboard \
  -H "Authorization: Bearer <token>"
# → All zeros

# Applicants (empty)
curl https://your-api.com/api/v1/applicants \
  -H "Authorization: Bearer <token>"
# → {"success": true, "data": {"items": [], "total": 0}}
```

### Frontend Verification

1. Open `https://your-domain.com` in Incognito/Private window
2. Verify login page loads
3. Login as admin
4. Verify dashboard shows all zeros
5. Verify Applicants page is empty
6. Verify Leads page is empty
7. Verify Employees page is empty

---

## Rollback Strategy

### Database
- Render's PostgreSQL (Supabase) supports Point-in-Time Recovery
- If migration fails, database is restored to previous state via transaction rollback

### Storage
- Supabase Storage stores all objects — use the `diagnose` endpoint to verify
- If documents are deleted accidentally, restore from Supabase Storage backups

### Frontend
- Render keeps the last 3 successful deploys
- Rollback via Render Dashboard → **Deploys** → **Rollback**

---

## Cold Start Optimization

The backend uses **background migrations** to improve cold start time:

1. App starts immediately (no blocking on migrations)
2. Migrations run in a background thread
3. `/ready` returns `503` until migrations complete
4. Once migrations finish, `/ready` returns `200`

This means:
- First request may arrive before migrations finish
- The request will still work (SQLAlchemy handles schema dynamically)
- `/ready` is the only endpoint that indicates migration status

---

## Monitoring

- **Render Dashboard**: Logs, metrics, and alerts
- **Supabase Dashboard**: Database performance and storage usage
- **Application Health**: GET `/health`, `/ready`, `/live`
