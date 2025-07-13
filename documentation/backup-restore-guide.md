# Production Backup and Restore Guide

## Overview

Production database backups are automated and stored in:
- **Hourly**: `backups/postgres/hourly/` (automatic, kept 7 days)
- **Weekly**: `backups/postgres/weekly/` (automatic, kept 90 days)
- **Manual**: `backups/postgres/manual/` (on-demand)

## Quick Commands

### Production Backups

```bash
# Create manual production backup
make backup-prod

# List all production backups
make list-backups

# Verify backup integrity
make backup-verify-prod BACKUP=20240115_143022
```

### Restore Operations

```bash
# Restore production (requires confirmation)
make restore-prod BACKUP=20240115_143022

# Restore to dev/test environments (for testing)
make restore-dev BACKUP=20240115_143022
make restore-test BACKUP=20240115_143022

# Test restore process safely
make test-restore-test
```

## Production Backup Schedule

- **Hourly backups**: Every hour at :00 (cron job inside postgres-prod container)
- **Weekly backups**: Sundays at 00:00
- **Manual backups**: On-demand via `make backup-prod`

## Restore Workflows

### 1. Emergency Production Restore

```bash
# List available backups
make list-backups

# Choose backup and restore (will ask for confirmation)
make restore-prod BACKUP=20240115_143022
```

**What happens:**
1. Verifies backup exists
2. Creates safety backup of current state
3. Stops application services (prevents duplicate imports)
4. Drops and recreates database
5. Restores from backup
6. Runs any missing migrations
7. Restarts services and checks health

### 2. Testing Restore Process

```bash
# Test in isolated environment
make test-restore-test
```

This safely tests the entire restore process without affecting real data.

### 3. Restore Production to Dev/Test

```bash
# Useful for debugging with production data
make restore-dev BACKUP=20240115_143022
make restore-test BACKUP=20240115_143022
```

## Important Notes

- **Import Protection**: Services automatically stop during restore to prevent duplicate imports
- **Safety Backup**: Always created before production restore
- **Migration Handling**: Automatically runs any migrations needed after restore
- **Backup Locations**: The restore commands check manual/, hourly/, and weekly/ folders

## Monitoring Backups

```bash
# Check if automated backups are running
docker exec postgres-prod tail -f /var/log/backup.log

# Verify cron is active
docker exec postgres-prod ps aux | grep crond

# List recent backups
make list-backups
```

## Troubleshooting

### Can't find backup?
```bash
make list-backups  # Shows all locations
```

### Verify backup before restore
```bash
make backup-verify-prod BACKUP=20240115_143022
```

### Check services after restore
```bash
make health-check
make status-prod
```

### Manual backup command failed?
Ensure postgres-prod container is running:
```bash
make status-prod
```