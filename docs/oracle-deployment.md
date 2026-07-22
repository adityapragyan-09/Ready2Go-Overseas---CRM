# Ready2Go CRM — Oracle Cloud Infrastructure Deployment Guide

## Prerequisites

- Oracle Cloud Infrastructure (OCI) account
- Docker and Docker Compose installed on OCI instance
- Domain name with DNS pointing to OCI instance
- SSL certificate (Let's Encrypt or OCI Load Balancer)
- PostgreSQL database (OCI Autonomous DB or OCI MySQL HeatWave)
- Object Storage bucket (OCI Object Storage for documents, or Supabase)

---

## Architecture Overview

```
Internet
    │
    ▼
OCI Load Balancer (HTTPS:443)
    │
    ▼
Nginx Reverse Proxy (container)
    ├── / → SPA frontend (static files)
    └── /api/ → Uvicorn backend (4 workers)
            │
            ▼
    PostgreSQL (OCI Autonomous DB)
    + OCI Object Storage (documents)
```

---

## Step 1: Provision OCI Resources

### Compute Instance
- **Shape**: VM.Standard.E4.Flex (2 OCPU, 16 GB RAM minimum)
- **OS**: Oracle Linux 8 or Ubuntu 22.04 LTS
- **Storage**: Block Volume, 100 GB minimum
- **Network**: Public subnet with security list rules

### Security List Rules

| Direction | Source/Dest | Port | Purpose |
|-----------|-------------|------|---------|
| Ingress | 0.0.0.0/0 | 443 | HTTPS |
| Ingress | 0.0.0.0/0 | 80 | HTTP redirect |
| Ingress | Load Balancer CIDR | 8000 | Backend API |
| Egress | 0.0.0.0/0 | 5432 | PostgreSQL |
| Egress | 0.0.0.0/0 | 443 | Object Storage API |

### Database (OCI Autonomous DB or PostgreSQL-compatible)
- Use OCI Autonomous Database (PostgreSQL-compatible) or a PostgreSQL VM
- Create database: `ready2go_crm`
- Configure connection pooling (PgBouncer recommended)

### Object Storage
- Create bucket: `ready2go-documents`
- Generate API key for bucket access
- Configure lifecycle rules for temporary file cleanup

---

## Step 2: Install Dependencies

```bash
# Install Docker
sudo dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo dnf install docker-ce docker-ce-cli containerd.io -y
sudo systemctl enable --now docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify
docker --version
docker-compose --version
```

---

## Step 3: Deploy Application

```bash
# Clone repository
git clone https://github.com/adityapragyan-09/Ready2Go-Overseas---CRM.git /opt/ready2go-crm
cd /opt/ready2go-crm

# Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env with production values (see Step 4)

# Create SSL directory
mkdir -p ssl
# Place SSL certificates in ssl/ directory

# Start services
docker-compose up -d --build

# Verify
docker-compose ps
docker-compose logs app
```

---

## Step 4: Environment Configuration

### `backend/.env` (Production)

```ini
ENVIRONMENT=production
DEBUG=false
APP_NAME="Ready2Go CRM"
APP_VERSION=1.0.0
API_PREFIX=/api/v1

# Security — generate with: openssl rand -hex 32
SECRET_KEY=<generate-random-64-char-hex>
JWT_SECRET_KEY=<generate-different-random-64-char-hex>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# Database — OCI Autonomous DB or PostgreSQL
DATABASE_URL=postgresql://user:password@host:5432/ready2go_crm

# CORS
FRONTEND_URL=https://your-domain.com

# Supabase Storage (or OCI Object Storage via S3-compatible API)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
SUPABASE_BUCKET=ready2go-documents

# Upload Limits
MAX_UPLOAD_SIZE_MB=500
UPLOAD_TIMEOUT_SECONDS=600
SIGNED_URL_EXPIRY_MINUTES=60
ALLOWED_DOCUMENT_TYPES=pdf,jpg,jpeg,png,doc,docx

# Pagination
DEFAULT_PAGE_SIZE=10
MAX_PAGE_SIZE=100
```

### `frontend/.env` (Production)

```ini
VITE_APP_NAME="Ready2Go CRM"
VITE_API_BASE_URL=https://your-domain.com/api/v1
VITE_MAX_UPLOAD_SIZE_MB=500
VITE_ALLOWED_DOCUMENT_TYPES=pdf,jpg,jpeg,png,doc,docx
VITE_API_TIMEOUT_MS=30000
VITE_DEFAULT_PAGE_SIZE=10
```

---

## Step 5: Database Migration

```bash
# Apply migrations
docker-compose exec app alembic upgrade head

# Verify migration status
docker-compose exec app alembic current

# Apply FK ondelete fixes for PostgreSQL
docker-compose exec app python -c "
# Run the ALTER TABLE statements from the migration docstring
# See backend/alembic/versions/eb6993635a25 for exact SQL
"
```

---

## Step 6: Configure SSL (Let's Encrypt)

```bash
# Install certbot
sudo dnf install certbot python3-certbot-nginx -y

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ssl/key.pem

# Uncomment SSL lines in nginx.conf
# Set auto-renewal
sudo crontab -e
# Add: 0 3 * * * certbot renew --quiet && docker-compose restart nginx
```

---

## Step 7: Verify Deployment

```bash
# Health check
curl https://your-domain.com/health
curl https://your-domain.com/ready
curl https://your-domain.com/live
curl https://your-domain.com/version

# Login test
curl -X POST https://your-domain.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"your-password"}'

# Frontend
curl https://your-domain.com/
```

---

## Step 8: PostgreSQL FK Fixes

After deploying with PostgreSQL, run these ALTER TABLE statements to fix the 11 FK ondelete drifts documented in the migration:

```sql
-- Run these in order on the PostgreSQL database
ALTER TABLE activity_logs DROP CONSTRAINT activity_logs_user_id_fkey,
  ADD CONSTRAINT fk_activity_logs_user_id
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;

ALTER TABLE applicants DROP CONSTRAINT applicants_assigned_to_fkey,
  ADD CONSTRAINT fk_applicants_assigned_to
  FOREIGN KEY (assigned_to) REFERENCES users(id) ON DELETE SET NULL;

ALTER TABLE applicants DROP CONSTRAINT applicants_created_by_fkey,
  ADD CONSTRAINT fk_applicants_created_by
  FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE RESTRICT;

ALTER TABLE applicants DROP CONSTRAINT applicants_deleted_by_fkey,
  ADD CONSTRAINT fk_applicants_deleted_by
  FOREIGN KEY (deleted_by) REFERENCES users(id) ON DELETE SET NULL;

ALTER TABLE documents DROP CONSTRAINT documents_applicant_id_fkey,
  ADD CONSTRAINT fk_documents_applicant_id
  FOREIGN KEY (applicant_id) REFERENCES applicants(id) ON DELETE CASCADE;

ALTER TABLE documents DROP CONSTRAINT documents_uploaded_by_fkey,
  ADD CONSTRAINT fk_documents_uploaded_by
  FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE RESTRICT;

ALTER TABLE documents DROP CONSTRAINT documents_deleted_by_fkey,
  ADD CONSTRAINT fk_documents_deleted_by
  FOREIGN KEY (deleted_by) REFERENCES users(id) ON DELETE SET NULL;

ALTER TABLE messages DROP CONSTRAINT messages_applicant_id_fkey,
  ADD CONSTRAINT fk_messages_applicant_id
  FOREIGN KEY (applicant_id) REFERENCES applicants(id) ON DELETE CASCADE;

ALTER TABLE messages DROP CONSTRAINT messages_sender_id_fkey,
  ADD CONSTRAINT fk_messages_sender_id
  FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE RESTRICT;

ALTER TABLE progress_history DROP CONSTRAINT progress_history_updated_by_fkey,
  ADD CONSTRAINT fk_progress_history_updated_by
  FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE RESTRICT;

ALTER TABLE users DROP CONSTRAINT users_created_by_fkey,
  ADD CONSTRAINT fk_users_created_by
  FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;
```

---

## Monitoring & Logging

### Health Probes
- `/health` — Application health (includes version)
- `/ready` — Readiness (includes database connection check)
- `/live` — Liveness (always returns 200)

### Logs
```bash
# Application logs
docker-compose logs -f app

# Nginx access logs (JSON format)
docker-compose logs -f nginx

# All services
docker-compose logs -f
```

### Resource Monitoring
```bash
# Container stats
docker stats

# System resources
htop
df -h
free -m
```

---

## Backup & Disaster Recovery

### Database Backup
```bash
# Daily backup
docker-compose exec app pg_dump -h host -U user ready2go_crm > /backups/crm_$(date +%Y%m%d).sql

# Keep 30 days of backups
find /backups -name "crm_*.sql" -mtime +30 -delete
```

### Database Restore
```bash
# Restore from backup
psql -h host -U user ready2go_crm < /backups/crm_20240101.sql
alembic upgrade head
```

### Application Rollback
```bash
# Rollback to previous version
cd /opt/ready2go-crm
git checkout <previous-release-tag>
docker-compose up -d --build
alembic upgrade head
```

---

## Troubleshooting

| Issue | Resolution |
|-------|-----------|
| Backend won't start | Check `docker-compose logs app` for migration errors or missing env vars |
| Database connection failed | Verify DATABASE_URL, network security list rules, and PostgreSQL is running |
| File upload fails | Check SUPABASE_URL/KEY, bucket permissions, and CORS headers |
| CORS error | Verify FRONTEND_URL matches the actual frontend domain |
| SSL error | Check certificate files in `ssl/` directory and nginx config |
| 502 Bad Gateway | Backend is unavailable — check `docker-compose logs app` |

---

## Scaling

### Vertical Scaling
- Increase OCPU/memory in OCI compute shape
- Increase `--workers` in startup.sh (rule: 2 × CPU cores + 1)

### Horizontal Scaling
- Deploy multiple app containers behind OCI Load Balancer
- Move PostgreSQL to OCI Autonomous DB for managed scaling
- Use OCI Object Storage for file storage
- Rate limiter is in-memory — switch to Redis-based for multi-worker deployments

---

## Security Checklist

- [ ] All secrets in environment variables (not in code)
- [ ] HTTPS enforced (redirect from HTTP)
- [ ] SSL certificates valid and auto-renewing
- [ ] CORS restricted to frontend domain
- [ ] Security headers enabled (HSTS, CSP, XFO)
- [ ] Rate limiting configured (30 req/s general, 5 req/m login)
- [ ] File uploads restricted to allowed types and sizes
- [ ] Database access restricted to app server IP
- [ ] Object Storage bucket not publicly accessible
- [ ] Backend API docs disabled in production
- [ ] Health endpoints don't leak sensitive data
- [ ] Logging doesn't include passwords or tokens
