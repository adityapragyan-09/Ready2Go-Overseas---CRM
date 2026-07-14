# Ready2Go CRM — Production Deployment Guide

## Deployment Target

| Component | Platform | Service Type |
|---|---|---|
| **Backend API** | Render | Web Service (Python) |
| **Frontend SPA** | Vercel or Netlify | Static Site |
| **Database** | Supabase | PostgreSQL |
| **File Storage** | Supabase | Storage |

---

## Required Environment Variables

### Backend (Render Dashboard → Environment)

| Variable | Required | Description | Example |
|---|---|---|---|
| `ENVIRONMENT` | ✅ | Set to `production` | `production` |
| `DEBUG` | ✅ | Set to `false` | `false` |
| `SECRET_KEY` | ✅ | Random 64-char hex string | `openssl rand -hex 32` |
| `JWT_SECRET_KEY` | ✅ | Different random 64-char hex | `openssl rand -hex 32` |
| `DATABASE_URL` | ✅ | Supabase PostgreSQL URL | `postgresql://...:6543/postgres?pgbouncer=true` |
| `FRONTEND_URL` | ✅ | Your frontend URL | `https://your-app.vercel.app` |
| `SUPABASE_URL` | ✅ | Supabase project URL | `https://your-project.supabase.co` |
| `SUPABASE_KEY` | ✅ | Service role key (NOT anon) | `eyJhbGciOiJIUzI1NiIs...` |
| `SUPABASE_BUCKET` | ❌ | Storage bucket name (default: `ready2go-documents`) | `ready2go-documents` |
| `APP_NAME` | ❌ | Default: `Ready2Go CRM` | `Ready2Go CRM` |
| `API_PREFIX` | ❌ | Default: `/api/v1` | `/api/v1` |
| `MAX_UPLOAD_SIZE_MB` | ❌ | Default: `500` | `500` |
| `SIGNED_URL_EXPIRY_MINUTES` | ❌ | Default: `60` | `60` |
| `PYTHON_VERSION` | ✅ | Set to `3.11.0` in Render | `3.11.0` |

### Frontend (Vercel/Netlify Dashboard → Environment Variables)

| Variable | Required | Description | Example |
|---|---|---|---|
| `VITE_API_BASE_URL` | ✅ | Backend API URL | `https://your-app.onrender.com/api/v1` |
| `VITE_APP_NAME` | ❌ | Browser tab title | `Ready2Go CRM` |
| `VITE_MAX_UPLOAD_SIZE_MB` | ❌ | Client-side upload limit | `500` |
| `VITE_API_TIMEOUT_MS` | ❌ | Request timeout in ms | `600000` |

---

## Deployment Steps

### Step 1: Database Setup (Supabase)

1. Create a Supabase project at [app.supabase.com](https://app.supabase.com)
2. Note your **Project URL** (e.g., `https://xyzabc.supabase.co`)
3. Get your **Service Role Key** (Settings → API → `service_role` key — NOT the `anon` key)
4. Get your **Database Connection String** (Project Settings → Database → Connection string → URI)
5. Enable connection pooling: Use port `6543` and append `?pgbouncer=true` to the URL

### Step 2: Backend Deployment (Render)

1. Push code to GitHub (already done)
2. Go to [Render Dashboard](https://dashboard.render.com) → New + → Web Service
3. Connect your GitHub repository
4. Configure:

| Setting | Value |
|---|---|
| **Name** | `ready2go-crm-api` |
| **Region** | Choose closest to your users |
| **Branch** | `main` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt && alembic upgrade head` |
| **Start Command** | `uvicorn main:app --host 0.0.0.0 --port $PORT --workers 4 --proxy-headers --forwarded-allow-ips "*"` |
| **Plan** | Starter or higher |

5. Add all **Backend Environment Variables** from the table above
6. Click **Create Web Service**

### Step 3: Run Database Migrations

Render will run `alembic upgrade head` during build. If it fails:

```bash
# Via Render Shell
cd backend && alembic upgrade head

# Or connect to the database directly
psql "$DATABASE_URL" -f backend/alembic/versions/*.sql
```

### Step 4: Create First Admin User

After deployment, create the initial admin:

```bash
# Via Render Shell
python backend/scripts/create_admin.py

# Or from your local machine with production DATABASE_URL set
DATABASE_URL="$PROD_DB_URL" python backend/scripts/create_admin.py
```

Default admin credentials (change immediately):
- Email: `admin@ready2gooverseas.com`
- Password: Check `ADMIN_PASSWORD` env var

### Step 5: Frontend Deployment (Vercel)

1. Go to [Vercel Dashboard](https://vercel.com) → Add New → Project
2. Import your GitHub repository
3. Configure:

| Setting | Value |
|---|---|
| **Framework Preset** | `Vite` |
| **Root Directory** | `frontend` |
| **Build Command** | `npm run build` |
| **Output Directory** | `dist` |

4. Add `VITE_API_BASE_URL` environment variable pointing to your Render backend
5. Click **Deploy**

### Step 6: Frontend Deployment (Netlify — Alternative)

1. Go to [Netlify Dashboard](https://app.netlify.com) → Add new site → Import from Git
2. Connect your repository
3. Configure:

| Setting | Value |
|---|---|
| **Base directory** | `frontend/` |
| **Build command** | `npm run build` |
| **Publish directory** | `frontend/dist` |

4. Add environment variable: `VITE_API_BASE_URL`
5. Add redirect rule in `frontend/public/_redirects`:
   ```
   /*    /index.html   200
   ```

---

## Post-Deployment Verification

### Health Checks

```bash
# Basic health
curl https://your-app.onrender.com/health

# Readiness (verifies database connection)
curl https://your-app.onrender.com/ready

# Liveness
curl https://your-app.onrender.com/live

# Version info
curl https://your-app.onrender.com/version
```

### Verify API

```bash
# Test login (after creating admin user)
curl -X POST https://your-app.onrender.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@ready2gooverseas.com", "password": "your-admin-password"}'
```

---

## Troubleshooting

### Backend won't start
- Check all required environment variables are set in Render dashboard
- Verify `DATABASE_URL` is a valid PostgreSQL URL (not SQLite)
- Check Render logs for import errors

### Database connection fails
- Ensure `?pgbouncer=true` is appended to the Supabase connection string
- Verify IP access settings in Supabase (allow all traffic for Render)
- Check database user has proper permissions

### Frontend shows blank page
- Verify `VITE_API_BASE_URL` is set correctly
- Check browser console for CORS errors
- Verify `FRONTEND_URL` on the backend matches your frontend domain

### File uploads fail
- Verify `SUPABASE_URL` and `SUPABASE_KEY` are the service role key
- Check Supabase Storage bucket exists and has proper RLS policies
- Ensure `SUPABASE_BUCKET` name matches

### Migration errors
- Run `alembic history` to check current state
- Run `alembic upgrade head` manually via Render Shell
- Check for conflicting migration revisions

---

## Production Checklist

- [ ] All environment variables configured in Render
- [ ] `ENVIRONMENT=production` and `DEBUG=false`
- [ ] `SECRET_KEY` and `JWT_SECRET_KEY` are strong random values
- [ ] `DATABASE_URL` points to Supabase PostgreSQL (not SQLite)
- [ ] Database migrations executed (`alembic upgrade head`)
- [ ] Admin user created
- [ ] Health endpoints responding
- [ ] Frontend `VITE_API_BASE_URL` points to backend
- [ ] CORS configured: `FRONTEND_URL` matches frontend domain
- [ ] File uploads working (Supabase Storage)
- [ ] SSL/HTTPS enabled (automatic on Render + Vercel)
- [ ] Backup schedule configured (see [backup-recovery.md](./backup-recovery.md))
