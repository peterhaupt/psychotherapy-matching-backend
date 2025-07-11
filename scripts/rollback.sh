#!/bin/bash
set -e

if [ -z "$1" ]; then
    echo "Usage: ./scripts/rollback.sh TIMESTAMP"
    echo "Example: ./scripts/rollback.sh 20240115_143022"
    echo ""
    echo "Available backups:"
    ls -la ./backups/postgres/backup_*.sql.gz 2>/dev/null | awk '{print "  - " $9}' || echo "  No backups found"
    exit 1
fi

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
cd "$PROJECT_ROOT"

TIMESTAMP=$1
BACKUP_FILE="./backups/postgres/backup_$TIMESTAMP.sql.gz"
COMPOSE_PROD="docker-compose -f docker-compose.prod.yml --env-file .env.prod"

echo "🔙 Rolling back backend to backup: $TIMESTAMP"
echo "============================================"

# Check if backup exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Backup file not found: $BACKUP_FILE"
    echo ""
    echo "Available backups:"
    ls -la ./backups/postgres/backup_*.sql.gz 2>/dev/null | awk '{print "  - " $9}' || echo "  No backups found"
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
echo "📥 Restoring database..."
# Drop existing connections and recreate database
docker exec postgres-prod psql -U ${DB_USER} -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='${DB_NAME}' AND pid <> pg_backend_pid();" postgres
docker exec postgres-prod psql -U ${DB_USER} -c "DROP DATABASE IF EXISTS ${DB_NAME};" postgres
docker exec postgres-prod psql -U ${DB_USER} -c "CREATE DATABASE ${DB_NAME};" postgres

# Restore from backup
gunzip -c "$BACKUP_FILE" | docker exec -i postgres-prod psql -U ${DB_USER} ${DB_NAME}

# Start all services
echo "🔄 Starting all services..."
$COMPOSE_PROD up -d

# Wait for services
echo "⏳ Waiting for services to start..."
sleep 15

# Health check
echo "❤️  Running health checks..."
SERVICES=(
    "patient:8011"
    "therapist:8012"
    "matching:8013"
    "communication:8014"
    "geocoding:8015"
)

ALL_HEALTHY=true
for SERVICE in "${SERVICES[@]}"; do
    IFS=':' read -r NAME PORT <<< "$SERVICE"
    echo -n "Checking $NAME service... "
    
    if curl -s -f "http://localhost:$PORT/health" > /dev/null 2>&1; then
        echo "✅ Healthy"
    else
        echo "❌ Failed"
        ALL_HEALTHY=false
    fi
done

echo ""
echo "============================================"
if $ALL_HEALTHY; then
    echo "✅ Backend rollback complete!"
    echo "All services restored to backup from $TIMESTAMP"
else
    echo "⚠️  Rollback completed but some services are unhealthy"
    echo "Check logs with: docker-compose -f docker-compose.prod.yml --env-file .env.prod logs"
fi
echo "============================================"