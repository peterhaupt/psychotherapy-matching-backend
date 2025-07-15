#!/bin/bash
set -e

if [ -z "$1" ]; then
    echo "Usage: ./scripts/rollback.sh TIMESTAMP"
    echo "Example: ./scripts/rollback.sh 20240115_143022"
    echo ""
    echo "Available production backups:"
    echo ""
    echo "Manual Backups:"
    ls -la ./backups/postgres/manual/backup_*.sql.gz 2>/dev/null | awk '{print "  - " $9}' | sed 's|.*manual/backup_||g' | sed 's|\.sql\.gz||g' || echo "  No manual backups found"
    echo ""
    echo "Hourly Backups (last 10):"
    ls -la ./backups/postgres/hourly/backup_*.sql.gz 2>/dev/null | tail -10 | awk '{print "  - " $9}' | sed 's|.*hourly/backup_||g' | sed 's|\.sql\.gz||g' || echo "  No hourly backups found"
    echo ""
    echo "Weekly Backups:"
    ls -la ./backups/postgres/weekly/weekly_backup_*.sql.gz 2>/dev/null | awk '{print "  - " $9}' | sed 's|.*weekly/weekly_backup_||g' | sed 's|\.sql\.gz||g' || echo "  No weekly backups found"
    exit 1
fi

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
cd "$PROJECT_ROOT"

TIMESTAMP=$1
COMPOSE_PROD="docker-compose -f docker-compose.prod.yml --env-file .env.prod"

echo "🔙 Rolling back backend to backup: $TIMESTAMP"
echo "============================================"

# Function to find backup file
find_backup_file() {
    local timestamp=$1
    
    # Check manual backups first
    if [ -f "./backups/postgres/manual/backup_$timestamp.sql.gz" ]; then
        echo "./backups/postgres/manual/backup_$timestamp.sql.gz"
        return 0
    fi
    
    # Check hourly backups
    if [ -f "./backups/postgres/hourly/backup_$timestamp.sql.gz" ]; then
        echo "./backups/postgres/hourly/backup_$timestamp.sql.gz"
        return 0
    fi
    
    # Check weekly backups (different naming pattern)
    if [ -f "./backups/postgres/weekly/weekly_backup_$timestamp.sql.gz" ]; then
        echo "./backups/postgres/weekly/weekly_backup_$timestamp.sql.gz"
        return 0
    fi
    
    return 1
}

# Find the backup file
BACKUP_FILE=$(find_backup_file "$TIMESTAMP")
if [ $? -ne 0 ]; then
    echo "❌ Backup file not found for timestamp: $TIMESTAMP"
    echo ""
    echo "Available production backups:"
    echo ""
    echo "Manual Backups:"
    ls -la ./backups/postgres/manual/backup_*.sql.gz 2>/dev/null | awk '{print "  - " $9}' | sed 's|.*manual/backup_||g' | sed 's|\.sql\.gz||g' || echo "  No manual backups found"
    echo ""
    echo "Hourly Backups (last 10):"
    ls -la ./backups/postgres/hourly/backup_*.sql.gz 2>/dev/null | tail -10 | awk '{print "  - " $9}' | sed 's|.*hourly/backup_||g' | sed 's|\.sql\.gz||g' || echo "  No hourly backups found"
    echo ""
    echo "Weekly Backups:"
    ls -la ./backups/postgres/weekly/weekly_backup_*.sql.gz 2>/dev/null | awk '{print "  - " $9}' | sed 's|.*weekly/weekly_backup_||g' | sed 's|\.sql\.gz||g' || echo "  No weekly backups found"
    exit 1
fi

echo "📁 Found backup file: $BACKUP_FILE"

# Verify backup integrity
echo "🔍 Verifying backup integrity..."
if gunzip -t "$BACKUP_FILE" 2>/dev/null; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "✅ Backup file is valid (Size: $BACKUP_SIZE)"
else
    echo "❌ Backup file is corrupted!"
    exit 1
fi

# Get database credentials from .env.prod
source .env.prod

# Stop production
echo "🛑 Stopping production services..."
$COMPOSE_PROD down

# Start just postgres
echo "🗄️  Starting database..."
$COMPOSE_PROD up -d postgres-prod
sleep 10  # Give postgres time to fully start

# Wait for postgres to be ready
echo "⏳ Waiting for database to be ready..."
for i in {1..30}; do
    if docker exec postgres-prod pg_isready -U ${DB_USER} > /dev/null 2>&1; then
        echo "✅ Database is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Database failed to start"
        exit 1
    fi
    sleep 1
done

# Restore database
echo "📥 Restoring database from backup..."
# Drop existing connections and recreate database
docker exec postgres-prod psql -U ${DB_USER} -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='${DB_NAME}' AND pid <> pg_backend_pid();" postgres
docker exec postgres-prod psql -U ${DB_USER} -c "DROP DATABASE IF EXISTS ${DB_NAME};" postgres
docker exec postgres-prod psql -U ${DB_USER} -c "CREATE DATABASE ${DB_NAME};" postgres

# Restore from backup
echo "📤 Importing backup data..."
gunzip -c "$BACKUP_FILE" | docker exec -i postgres-prod psql -U ${DB_USER} ${DB_NAME}
echo "✅ Database restored successfully"

# Run migrations to ensure database is up to date
echo "📊 Running migrations..."
export $(cat .env.prod | grep -v '^#' | xargs)
cd migrations && ENV=prod alembic upgrade head && cd ..
if [ $? -eq 0 ]; then
    echo "✅ Migrations completed successfully"
else
    echo "❌ Migration failed!"
    exit 1
fi

# Start all services
echo "🔄 Starting all services..."
$COMPOSE_PROD up -d

# Wait for services
echo "⏳ Waiting for services to start..."
sleep 15

# Health check
echo "❤️  Running health checks..."
SERVICES=(
    "patient:8021"
    "therapist:8022"
    "matching:8023"
    "communication:8024"
    "geocoding:8025"
)

ALL_HEALTHY=true
for SERVICE in "${SERVICES[@]}"; do
    IFS=':' read -r NAME PORT <<< "$SERVICE"
    echo -n "Checking $NAME service... "
    
    HEALTHY=false
    for i in $(seq 1 30); do
        if curl -s -f "http://localhost:$PORT/health" > /dev/null 2>&1; then
            HEALTHY=true
            break
        fi
        sleep 2
    done
    
    if $HEALTHY; then
        echo "✅ Healthy"
    else
        echo "❌ Failed"
        ALL_HEALTHY=false
    fi
done

# Check backup container
echo -n "Checking backup service... "
if docker ps | grep -q postgres-backup-prod; then
    if curl -s -f "http://localhost:8080/health" > /dev/null 2>&1; then
        echo "✅ Healthy"
    else
        echo "⚠️  Health check failed (container running but no response)"
    fi
else
    echo "⚠️  Container not running"
fi

echo ""
echo "============================================"
if $ALL_HEALTHY; then
    echo "✅ Backend rollback complete!"
    echo "All services restored to backup from $TIMESTAMP"
    echo ""
    echo "Backup source: $BACKUP_FILE"
else
    echo "⚠️  Rollback completed but some services are unhealthy"
    echo "Check logs with: docker-compose -f docker-compose.prod.yml --env-file .env.prod logs"
fi
echo "============================================"