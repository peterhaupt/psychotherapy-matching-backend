#!/bin/bash
set -e

echo "🚀 Curavani Backend Production Deployment Starting..."
echo "===================================================="

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
cd "$PROJECT_ROOT"

BACKUP_DIR="./backups/postgres"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
COMPOSE_PROD="docker-compose -f docker-compose.prod.yml --env-file .env.prod"
HEALTH_CHECK_RETRIES=30
HEALTH_CHECK_DELAY=2

# 1. Backup production database (if exists)
echo ""
echo "💾 Backing up production database..."
echo "-----------------------------------"
mkdir -p "$BACKUP_DIR"

# Check if production is running
if docker ps | grep -q postgres-prod; then
    # Get database credentials from .env.prod
    source .env.prod
    docker exec postgres-prod pg_dump -U ${DB_USER} ${DB_NAME} | gzip > "$BACKUP_DIR/backup_$TIMESTAMP.sql.gz"
    echo "✅ Backup saved to: $BACKUP_DIR/backup_$TIMESTAMP.sql.gz"
else
    echo "⚠️  No production database running, skipping backup"
fi

# 2. Build production images
echo ""
echo "🏗️  Building production images..."
echo "--------------------------------"
$COMPOSE_PROD build

# 3. Stop production services
echo ""
echo "🛑 Stopping current production services..."
echo "-----------------------------------------"
$COMPOSE_PROD down

# 4. Start new production services
echo ""
echo "🔄 Starting new production services..."
echo "-------------------------------------"
$COMPOSE_PROD up -d

# 5. Wait for services to be ready
echo ""
echo "⏳ Waiting for services to be healthy..."
echo "---------------------------------------"
sleep 15  # Give services time to fully start

# 6. Run Alembic migrations
echo ""
echo "🗃️  Running database migrations..."
echo "---------------------------------"
# Load production environment variables for migrations
export $(cat .env.prod | grep -v '^#' | xargs)
cd migrations && ENV=prod alembic upgrade head && cd ..
if [ $? -eq 0 ]; then
    echo "✅ Migrations completed successfully"
else
    echo "❌ Migration failed!"
    exit 1
fi

# 7. Verify migration status
echo ""
echo "🔍 Verifying migration status..."
echo "--------------------------------"
cd migrations && ENV=prod alembic current && cd ..

# 8. Health checks
echo ""
echo "❤️  Running health checks..."
echo "---------------------------"

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
    for i in $(seq 1 $HEALTH_CHECK_RETRIES); do
        if curl -s -f "http://localhost:$PORT/health" > /dev/null 2>&1; then
            HEALTHY=true
            break
        fi
        sleep $HEALTH_CHECK_DELAY
    done
    
    if $HEALTHY; then
        echo "✅ Healthy"
    else
        echo "❌ Failed"
        ALL_HEALTHY=false
    fi
done

# 9. Run smoke tests if services are healthy
if $ALL_HEALTHY; then
    echo ""
    echo "🧪 Running smoke tests in production..."
    echo "--------------------------------------"
    
    # Run smoke tests against production endpoints
    SMOKE_TEST_FAILED=false
    
    # Set production environment variables for tests
    export PATIENT_API_URL="http://localhost:8021/api"
    export THERAPIST_API_URL="http://localhost:8022/api"
    export MATCHING_API_URL="http://localhost:8023/api"
    export COMMUNICATION_API_URL="http://localhost:8024/api"
    export GEOCODING_API_URL="http://localhost:8025/api"
    
    # Set health URLs for smoke tests
    export PATIENT_HEALTH_URL="http://localhost:8021/health"
    export THERAPIST_HEALTH_URL="http://localhost:8022/health"
    export MATCHING_HEALTH_URL="http://localhost:8023/health"
    export COMMUNICATION_HEALTH_URL="http://localhost:8024/health"
    export GEOCODING_HEALTH_URL="http://localhost:8025/health"
    
    # Run smoke tests from the host
    if command -v pytest &> /dev/null; then
        pytest ./tests/smoke -v --tb=short --env=prod || SMOKE_TEST_FAILED=true
    else
        echo "⚠️  pytest not found locally"
        echo "    Please ensure pytest is installed: pip install pytest"
        SMOKE_TEST_FAILED=true
    fi
    
    if $SMOKE_TEST_FAILED; then
        echo "⚠️  Some smoke tests failed, but deployment completed"
        ALL_HEALTHY=false
    else
        echo "✅ All smoke tests passed!"
    fi
fi

# 10. Final status
echo ""
echo "===================================================="
if $ALL_HEALTHY; then
    echo "✅ BACKEND DEPLOYMENT SUCCESSFUL!"
    echo "All services are running and healthy."
    echo ""
    echo "Backend API endpoints available at:"
    echo "  - Patient Service: http://localhost:8021/api"
    echo "  - Therapist Service: http://localhost:8022/api"
    echo "  - Matching Service: http://localhost:8023/api"
    echo "  - Communication Service: http://localhost:8024/api"
    echo "  - Geocoding Service: http://localhost:8025/api"
    echo ""
    echo "Automatic database backups are configured inside the postgres container."
else
    echo "❌ BACKEND DEPLOYMENT COMPLETED WITH WARNINGS!"
    echo "Some services failed health checks or smoke tests failed."
    echo ""
    echo "Check logs with: docker-compose -f docker-compose.prod.yml --env-file .env.prod logs"
    echo ""
    echo "To rollback, run: ./scripts/rollback.sh $TIMESTAMP"
fi
echo "===================================================="

# Exit with appropriate code
if $ALL_HEALTHY; then
    exit 0
else
    exit 1
fi