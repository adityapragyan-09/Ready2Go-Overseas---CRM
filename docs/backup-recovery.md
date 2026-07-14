# Ready2Go CRM — Backup & Recovery Guide

## Overview

This document outlines the backup and recovery procedures for the Ready2Go CRM production system.

## 1. PostgreSQL Database Backup

### Automated Daily Backup (Recommended)

```bash
# Using pg_dump
pg_dump "postgresql://user:password@host:5432/ready2go_crm" \
    --format=custom \
    --file=/backups/crm_$(date +%Y%m%d_%H%M%S).dump \
    --verbose \
    --no-owner
```

### Backup via Cron

Add to crontab for daily backups at 2 AM:

```cron
0 2 * * * pg_dump "postgresql://user:password@host:5432/ready2go_crm" --format=custom --file=/backups/crm_$(date +\%Y\%m\%d).dump --no-owner && find /backups -name "crm_*.dump" -mtime +30 -delete
```

### Retention Policy

- Daily backups: retain 30 days
- Weekly backups: retain 12 weeks
- Monthly backups: retain 12 months

## 2. Supabase Backup

### Database Backups (Supabase Dashboard)

Supabase provides automated daily backups for Pro plans and above. To manually trigger:

1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Select your project
3. Navigate to **Database → Backups**
4. Click **Create backup**

### Point-in-Time Recovery (PITR)

For PITR, enable the add-on in Supabase:

1. **Database → Backups → Point-in-Time Recovery**
2. Enable PITR (retains WAL logs for 7 days)
3. Recovery point is selectable within the retention window

## 3. Storage Backups

### Supabase Storage Backup

```bash
# Download all files from a bucket using supabase CLI
npx supabase storage download ready2go-documents ./backups/storage/

# Or use the API directly
curl -X GET "$SUPABASE_URL/storage/v1/object/ready2go-documents" \
  -H "Authorization: Bearer $SUPABASE_KEY"
```

### Filesystem Backups (Local/Dev)

```bash
# Backup uploads directory
tar -czf /backups/uploads_$(date +%Y%m%d).tar.gz /app/uploads/
```

## 4. Complete Restore Process

### Restore Database

```bash
# Drop and recreate database
dropdb ready2go_crm
createdb ready2go_crm

# Restore from custom format dump
pg_restore --dbname=postgresql://user:password@host:5432/ready2go_crm \
    --format=custom \
    --clean \
    --if-exists \
    --verbose \
    /backups/crm_20240101.dump
```

### Run Migrations

```bash
# Ensure the schema is up to date
cd backend
alembic upgrade head

# Seed admin user if needed
python scripts/create_admin.py
```

### Verify Restoration

```bash
# Check record counts
python scripts/maintenance.py db-stats

# Verify API health
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

## 5. Disaster Recovery Plan

### Failure Scenarios

| Scenario | Recovery Action | RTO | RPO |
|---|---|---|---|
| Database corruption | Restore from latest backup | 1 hour | 24 hours |
| Storage loss | Restore from storage backup | 2 hours | 24 hours |
| Full system failure | Deploy new instance, restore DB + storage | 4 hours | 24 hours |
| Region failure | Deploy to secondary region, restore from off-site backup | 8 hours | 1 hour |

### Step-by-Step Full Recovery

1. **Provision new infrastructure**
   ```bash
   docker-compose up -d
   ```

2. **Restore database**
   ```bash
   pg_restore --dbname=$DATABASE_URL --format=custom --clean /backups/latest.dump
   ```

3. **Run migrations**
   ```bash
   cd backend && alembic upgrade head
   ```

4. **Restore storage files**
   ```bash
   # Download from Supabase or restore from file backup
   ```

5. **Verify system health**
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:8000/ready
   curl http://localhost:8000/version
   ```

6. **Run integrity checks**
   ```bash
   python scripts/maintenance.py check-integrity
   ```

## 6. Maintenance Schedule

| Task | Frequency | Script |
|---|---|---|
| Cleanup old notifications | Weekly | `python scripts/maintenance.py cleanup-notifications` |
| Database statistics | Daily | `python scripts/maintenance.py db-stats` |
| Integrity check | Weekly | `python scripts/maintenance.py check-integrity` |
| Full database backup | Daily | pg_dump (see above) |
| Storage backup | Daily | Supabase automated backup |
