# Ready2Go CRM — Production Deployment Guide

## Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL (Supabase)
- Docker & Docker Compose (optional)

## Environment Variables

Copy and configure the environment file:

```bash
cp backend/.env.example backend/.env
```

Required variables:
- `SECRET_KEY` — Random 64-char hex string
- `JWT_SECRET_KEY` — Random 64-char hex string (different from SECRET_KEY)
- `DATABASE_URL` — Supabase PostgreSQL connection string
- `SUPABASE_URL` — Supabase project URL
- `SUPABASE_KEY` — Supabase service role key
- `FRONTEND_URL` — Production frontend URL

## Deployment Options

### Option 1: Docker Compose (Recommended)

```bash
# Build and start all services
docker-compose up -d --build

# Check logs
docker-compose logs -f app

# Run database migrations
docker-compose exec app python scripts/migrate.py

# Create admin user
docker-compose exec app python scripts/create_admin.py
```

### Option 2: Manual Deployment

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start the server
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Build for production
npm run build

# Serve via nginx (see nginx.conf)
```

### Option 3: Supabase + Vercel/Railway

1. **Database**: Use Supabase PostgreSQL
2. **Backend**: Deploy to Railway/Render as a web service
3. **Frontend**: Deploy to Vercel as a static site
4. **Storage**: Use Supabase Storage

## Health Checks

After deployment, verify:

```bash
# Basic health
curl https://your-domain.com/health

# Readiness
curl https://your-domain.com/ready

# Liveness
curl https://your-domain.com/live

# Version info
curl https://your-domain.com/version
```

## Post-Deployment Checklist

- [ ] Environment variables configured
- [ ] Database migrations executed
- [ ] Admin user created
- [ ] Health endpoints responding
- [ ] Frontend accessible
- [ ] API calls working (login, CRUD)
- [ ] File uploads working
- [ ] SSL certificate configured (if using custom domain)
- [ ] Backup schedule configured
- [ ] Monitoring alerts set up
