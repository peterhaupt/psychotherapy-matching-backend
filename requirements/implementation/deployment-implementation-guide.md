# Curavani Deployment Implementation Guide - Separated Approach

## Overview

This guide implements a two-environment setup (Development and Production) with complete separation and **independent deployment** for backend and frontend.

## Architecture Summary

- **Two separate repositories/directories**: `curavani_backend` and `curavani_frontend_internal`
- **Independent deployment**: Deploy frontend and backend separately
- **Development**: Runs on standard ports
- **Production**: Runs on alternate ports
- **No shared resources** between environments
- **Downtime**: Backend 30-60 seconds, Frontend zero downtime

## Port Mapping

| Service | Development | Production |
|---------|------------|------------|
| **Backend Services** | | |
| PostgreSQL | 5432 | 5433 |
| PgBouncer | 6432 | 6433 |
| Kafka | 9092 | 9093 |
| Zookeeper | 2181 | 2182 |
| Patient Service | 8001 | 8011 |
| Therapist Service | 8002 | 8012 |
| Matching Service | 8003 | 8013 |
| Communication Service | 8004 | 8014 |
| Geocoding Service | 8005 | 8015 |
| **Frontend** | | |
| React App | 3000 | 80 |

## File Structure

```
/
├── curavani_backend/
│   ├── docker-compose.dev.yml
│   ├── docker-compose.prod.yml
│   ├── .env.dev
│   ├── .env.prod
│   ├── Makefile
│   ├── scripts/
│   │   ├── deploy.sh
│   │   ├── rollback.sh
│   │   └── backup-hourly.sh
│   └── backups/
│       └── postgres/
│           ├── hourly/
│           └── weekly/
│
└── curavani_frontend_internal/
    ├── Dockerfile
    ├── nginx.conf
    ├── .env.development
    ├── .env.production
    ├── Makefile
    └── scripts/
        └── deploy.sh
```

---

# Part 1: Backend Setup (curavani_backend)

## Backend Step 1: Restructure Docker Compose Files

### 1.1 Move current docker-compose.yml
```bash
cd curavani_backend
mv docker-compose.yml docker-compose.dev.yml
```

### 1.2 Create docker-compose.prod.yml
Create a production compose file with:
- Container names suffixed with `-prod`
- Different ports for all services
- No hot-reload volume mounts
- Production environment variables

Key changes for production:
- `container_name: postgres` → `container_name: postgres-prod`
- `ports: "5432:5432"` → `ports: "5433:5432"`
- Remove volumes like `./patient_service:/app`
- Update all service references

## Backend Step 2: Environment Configuration

### 2.1 Create .env.dev
```bash
# Database
DB_USER=curavani_user
DB_PASSWORD=curavani_password
DB_NAME=curavani_dev
DB_HOST=postgres
DB_PORT=5432

# Services
PGBOUNCER_HOST=pgbouncer
PGBOUNCER_PORT=6432
KAFKA_BOOTSTRAP_SERVERS=kafka:9093
KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181

# Flask
FLASK_ENV=development
FLASK_DEBUG=True
LOG_LEVEL=DEBUG

# Keep all your existing variables...
```

### 2.2 Create .env.prod
```bash
# Database
DB_USER=curavani_prod_user
DB_PASSWORD=CHANGE_THIS_STRONG_PASSWORD
DB_NAME=curavani_prod
DB_HOST=postgres-prod
DB_PORT=5432

# Services - note the -prod suffix
PGBOUNCER_HOST=pgbouncer-prod
PGBOUNCER_PORT=6432
KAFKA_BOOTSTRAP_SERVERS=kafka-prod:9093
KAFKA_ZOOKEEPER_CONNECT=zookeeper-prod:2181

# Flask
FLASK_ENV=production
FLASK_DEBUG=False
LOG_LEVEL=INFO

# Keep all your existing variables...
```

Add to `.gitignore`:
```
.env.prod
backups/
```

## Backend Step 3: Create Backend Deployment Scripts

### 3.1 Create curavani_backend/scripts/deploy.sh
```bash
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
COMPOSE_DEV="docker-compose -f docker-compose.dev.yml --env-file .env.dev"
COMPOSE_PROD="docker-compose -f docker-compose.prod.yml --env-file .env.prod"
HEALTH_CHECK_RETRIES=30
HEALTH_CHECK_DELAY=2

# 1. Run tests in development
echo "🧪 Running tests in development environment..."
echo "-------------------------------------------"
$COMPOSE_DEV exec patient_service pytest /app/tests/integration/test_patient_service_api.py -v
$COMPOSE_DEV exec therapist_service pytest /app/tests/integration/test_therapist_service_api.py -v
$COMPOSE_DEV exec matching_service pytest /app/tests/integration/test_matching_service_api.py -v
$COMPOSE_DEV exec communication_service pytest /app/tests/integration/test_communication_service_api.py -v
$COMPOSE_DEV exec geocoding_service pytest /app/tests/integration/test_geocoding_service_api.py -v

# Database schema test
$COMPOSE_DEV exec patient_service pytest /app/tests/integration/test_database_schemas.py -v

echo "✅ All backend tests passed!"

# 2. Backup production database
echo ""
echo "💾 Backing up production database..."
echo "-----------------------------------"
mkdir -p "$BACKUP_DIR"

# Check if production is running
if docker ps | grep -q postgres-prod; then
    docker exec postgres-prod pg_dump -U curavani_prod_user curavani_prod | gzip > "$BACKUP_DIR/backup_$TIMESTAMP.sql.gz"
    echo "✅ Backup saved to: $BACKUP_DIR/backup_$TIMESTAMP.sql.gz"
else
    echo "⚠️  No production database running, skipping backup"
fi

# 3. Build production images
echo ""
echo "🏗️  Building production images..."
echo "--------------------------------"
$COMPOSE_PROD build

# 4. Stop production services
echo ""
echo "🛑 Stopping current production services..."
echo "-----------------------------------------"
$COMPOSE_PROD down

# 5. Start new production services
echo ""
echo "🔄 Starting new production services..."
echo "-------------------------------------"
$COMPOSE_PROD up -d

# 6. Wait for services to be ready
echo ""
echo "⏳ Waiting for services to be healthy..."
echo "---------------------------------------"
sleep 10

# 7. Health checks
echo ""
echo "❤️  Running health checks..."
echo "---------------------------"

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

# 8. Final status
echo ""
echo "===================================================="
if $ALL_HEALTHY; then
    echo "✅ BACKEND DEPLOYMENT SUCCESSFUL!"
    echo "All services are running and healthy."
    echo ""
    echo "Backend API endpoints available at:"
    echo "  - Patient Service: http://localhost:8011/api"
    echo "  - Therapist Service: http://localhost:8012/api"
    echo "  - Matching Service: http://localhost:8013/api"
    echo "  - Communication Service: http://localhost:8014/api"
    echo "  - Geocoding Service: http://localhost:8015/api"
else
    echo "❌ BACKEND DEPLOYMENT FAILED!"
    echo "Some services failed health checks."
    echo ""
    echo "To rollback, run: ./scripts/rollback.sh $TIMESTAMP"
fi
echo "===================================================="
```

### 3.2 Create curavani_backend/scripts/rollback.sh
```bash
#!/bin/bash
set -e

if [ -z "$1" ]; then
    echo "Usage: ./scripts/rollback.sh TIMESTAMP"
    echo "Example: ./scripts/rollback.sh 20240115_143022"
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
    exit 1
fi

# Stop production
echo "🛑 Stopping production services..."
$COMPOSE_PROD down

# Start just postgres
echo "🗄️  Starting database..."
$COMPOSE_PROD up -d postgres-prod
sleep 5

# Restore database
echo "📥 Restoring database..."
docker exec postgres-prod psql -U curavani_prod_user -c "DROP DATABASE IF EXISTS curavani_prod;"
docker exec postgres-prod psql -U curavani_prod_user -c "CREATE DATABASE curavani_prod;"
gunzip -c "$BACKUP_FILE" | docker exec -i postgres-prod psql -U curavani_prod_user curavani_prod

# Start all services
echo "🔄 Starting all services..."
$COMPOSE_PROD up -d

echo "✅ Backend rollback complete!"
```

### 3.3 Create curavani_backend/scripts/backup-hourly.sh
```bash
#!/bin/bash
# Add to cron: 0 * * * * /path/to/curavani_backend/scripts/backup-hourly.sh

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
cd "$PROJECT_ROOT"

BACKUP_DIR="./backups/postgres/hourly"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"
mkdir -p "./backups/postgres/weekly"

# Create backup if production is running
if docker ps | grep -q postgres-prod; then
    docker exec postgres-prod pg_dump -U curavani_prod_user curavani_prod | \
        gzip > "$BACKUP_DIR/backup_$TIMESTAMP.sql.gz"
    
    # Keep only last 7 days of hourly backups
    find "$BACKUP_DIR" -name "backup_*.sql.gz" -mtime +7 -delete
    
    # Keep weekly backups for 3 months (run on Sundays)
    if [ $(date +%w) -eq 0 ]; then
        cp "$BACKUP_DIR/backup_$TIMESTAMP.sql.gz" "./backups/postgres/weekly/"
        find "./backups/postgres/weekly" -name "backup_*.sql.gz" -mtime +90 -delete
    fi
fi
```

## Backend Step 4: Create Backend Makefile

Create `curavani_backend/Makefile`:
```makefile
.PHONY: dev prod test deploy rollback backup logs-dev logs-prod stop-dev stop-prod status

# Development commands
dev:
	docker-compose -f docker-compose.dev.yml --env-file .env.dev up

stop-dev:
	docker-compose -f docker-compose.dev.yml --env-file .env.dev down

logs-dev:
	docker-compose -f docker-compose.dev.yml --env-file .env.dev logs -f

# Production commands
prod:
	docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d

stop-prod:
	docker-compose -f docker-compose.prod.yml --env-file .env.prod down

logs-prod:
	docker-compose -f docker-compose.prod.yml --env-file .env.prod logs -f

# Testing
test:
	docker-compose -f docker-compose.dev.yml --env-file .env.dev exec patient_service pytest tests/integration -v

# Deployment
deploy:
	./scripts/deploy.sh

rollback:
	@echo "Usage: make rollback TIMESTAMP=20240115_143022"
	@[ -n "$(TIMESTAMP)" ] && ./scripts/rollback.sh $(TIMESTAMP) || echo "Error: TIMESTAMP required"

backup:
	./scripts/backup-hourly.sh

# Status
status:
	@echo "=== Backend Development Status ==="
	@docker-compose -f docker-compose.dev.yml --env-file .env.dev ps
	@echo ""
	@echo "=== Backend Production Status ==="
	@docker-compose -f docker-compose.prod.yml --env-file .env.prod ps
```

---

# Part 2: Frontend Setup (curavani_frontend_internal)

## Frontend Step 1: Create Production Build Configuration

### 1.1 Create Dockerfile
Create `curavani_frontend_internal/Dockerfile`:
```dockerfile
# Build stage
FROM node:18-alpine AS builder
WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy source code
COPY . .

# Build arguments for API endpoints (production backend ports)
ARG REACT_APP_PATIENT_API=http://localhost:8011/api
ARG REACT_APP_THERAPIST_API=http://localhost:8012/api
ARG REACT_APP_MATCHING_API=http://localhost:8013/api
ARG REACT_APP_COMMUNICATION_API=http://localhost:8014/api
ARG REACT_APP_GEOCODING_API=http://localhost:8015/api

# Set production environment
ENV NODE_ENV=production
ENV REACT_APP_USE_MOCK_DATA=false
ENV REACT_APP_PATIENT_API=$REACT_APP_PATIENT_API
ENV REACT_APP_THERAPIST_API=$REACT_APP_THERAPIST_API
ENV REACT_APP_MATCHING_API=$REACT_APP_MATCHING_API
ENV REACT_APP_COMMUNICATION_API=$REACT_APP_COMMUNICATION_API
ENV REACT_APP_GEOCODING_API=$REACT_APP_GEOCODING_API

# Build the app
RUN npm run build

# Production stage
FROM nginx:alpine
WORKDIR /usr/share/nginx/html

# Copy built app
COPY --from=builder /app/build .

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### 1.2 Create nginx.conf
Create `curavani_frontend_internal/nginx.conf`:
```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 10240;
    gzip_proxied expired no-cache no-store private auth;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    # Cache static assets
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Cache index.html for short time
    location = /index.html {
        expires 1h;
        add_header Cache-Control "public, must-revalidate";
    }

    # React app routing - try files, fallback to index.html
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
}
```

## Frontend Step 2: Environment Files

### 2.1 Update .env.development
```bash
# Development API endpoints
REACT_APP_PATIENT_API=http://localhost:8001/api
REACT_APP_THERAPIST_API=http://localhost:8002/api
REACT_APP_MATCHING_API=http://localhost:8003/api
REACT_APP_COMMUNICATION_API=http://localhost:8004/api
REACT_APP_GEOCODING_API=http://localhost:8005/api

# Development settings
REACT_APP_USE_MOCK_DATA=true
```

### 2.2 Create .env.production
```bash
# Production API endpoints (backend production ports)
REACT_APP_PATIENT_API=http://localhost:8011/api
REACT_APP_THERAPIST_API=http://localhost:8012/api
REACT_APP_MATCHING_API=http://localhost:8013/api
REACT_APP_COMMUNICATION_API=http://localhost:8014/api
REACT_APP_GEOCODING_API=http://localhost:8015/api

# Production settings
REACT_APP_USE_MOCK_DATA=false
```

## Frontend Step 3: Create Frontend Deployment Script

### 3.1 Create curavani_frontend_internal/scripts/deploy.sh
```bash
#!/bin/bash
set -e

echo "🚀 Curavani Frontend Production Deployment Starting..."
echo "===================================================="

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
cd "$PROJECT_ROOT"

CONTAINER_NAME="curavani-frontend-prod"
IMAGE_NAME="curavani-frontend:latest"
BACKUP_IMAGE="curavani-frontend:backup"

# 1. Test build
echo "🧪 Testing frontend build..."
echo "---------------------------"
npm run build
echo "✅ Frontend build successful!"

# 2. Create backup of current production (if exists)
echo ""
echo "💾 Backing up current production image..."
echo "---------------------------------------"
if docker images | grep -q "$IMAGE_NAME"; then
    docker tag "$IMAGE_NAME" "$BACKUP_IMAGE"
    echo "✅ Backup created: $BACKUP_IMAGE"
else
    echo "⚠️  No existing production image to backup"
fi

# 3. Build new production image
echo ""
echo "🏗️  Building new production image..."
echo "-----------------------------------"
docker build -t "$IMAGE_NAME" .

# 4. Stop current production (if running)
echo ""
echo "🛑 Stopping current production container..."
echo "-----------------------------------------"
if docker ps | grep -q "$CONTAINER_NAME"; then
    docker stop "$CONTAINER_NAME"
    docker rm "$CONTAINER_NAME"
    echo "✅ Stopped and removed old container"
else
    echo "⚠️  No running production container found"
fi

# 5. Start new production container
echo ""
echo "🔄 Starting new production container..."
echo "--------------------------------------"
docker run -d \
    --name "$CONTAINER_NAME" \
    -p 80:80 \
    --restart unless-stopped \
    "$IMAGE_NAME"

# 6. Health check
echo ""
echo "❤️  Running health check..."
echo "--------------------------"
sleep 3

if curl -s -f "http://localhost:80" > /dev/null 2>&1; then
    echo "✅ Frontend is healthy!"
    
    # Get container info
    echo ""
    echo "📊 Container Info:"
    docker ps --filter "name=$CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
else
    echo "❌ Frontend health check failed!"
    echo ""
    echo "Rolling back to previous version..."
    
    # Rollback
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    docker rm "$CONTAINER_NAME" 2>/dev/null || true
    
    if docker images | grep -q "$BACKUP_IMAGE"; then
        docker tag "$BACKUP_IMAGE" "$IMAGE_NAME"
        docker run -d --name "$CONTAINER_NAME" -p 80:80 --restart unless-stopped "$IMAGE_NAME"
        echo "✅ Rolled back to previous version"
    fi
fi

# 7. Final status
echo ""
echo "===================================================="
if curl -s -f "http://localhost:80" > /dev/null 2>&1; then
    echo "✅ FRONTEND DEPLOYMENT SUCCESSFUL!"
    echo "Frontend is available at: http://localhost:80"
    echo ""
    echo "Note: Users may need to clear browser cache or hard refresh (Ctrl+F5)"
else
    echo "❌ FRONTEND DEPLOYMENT FAILED!"
    echo "Check logs with: docker logs $CONTAINER_NAME"
fi
echo "===================================================="
```

## Frontend Step 4: Create Frontend Makefile

Create `curavani_frontend_internal/Makefile`:
```makefile
.PHONY: dev build test deploy logs status clean

# Development
dev:
	npm start

install:
	npm install

# Building
build:
	npm run build

build-docker:
	docker build -t curavani-frontend:latest .

# Testing
test:
	npm test -- --watchAll=false

lint:
	npm run lint

# Production
deploy:
	./scripts/deploy.sh

logs:
	docker logs -f curavani-frontend-prod

status:
	@echo "=== Frontend Status ==="
	@if docker ps | grep -q curavani-frontend-prod; then \
		echo "✅ Production frontend is running"; \
		docker ps --filter "name=curavani-frontend-prod" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"; \
	else \
		echo "❌ Production frontend is not running"; \
	fi

stop:
	docker stop curavani-frontend-prod && docker rm curavani-frontend-prod

# Utilities
clean:
	rm -rf build/
	rm -rf node_modules/
	docker rmi curavani-frontend:backup 2>/dev/null || true
```

---

# Usage Guide

## Development Workflow

### Backend Development
```bash
cd curavani_backend
make dev                 # Start all backend services
make logs-dev           # View logs
make test               # Run tests
make stop-dev           # Stop services
```

### Frontend Development
```bash
cd curavani_frontend_internal
make dev                # Start React dev server (port 3000)
```

## Deployment Workflow

### Deploy Backend Only
```bash
cd curavani_backend
make deploy             # Tests → Backup → Deploy → Health Check
```

### Deploy Frontend Only
```bash
cd curavani_frontend_internal
make deploy             # Build → Backup Image → Deploy → Health Check
```

### Check Production Status
```bash
# Backend
cd curavani_backend
make status            # Shows all services
make logs-prod         # View production logs

# Frontend
cd curavani_frontend_internal
make status            # Shows container status
make logs              # View nginx/react logs
```

### Rollback Procedures

#### Backend Rollback
```bash
cd curavani_backend
# Find backup timestamp in backups/postgres/
make rollback TIMESTAMP=20240115_143022
```

#### Frontend Rollback
Frontend automatically rolls back if health check fails. For manual rollback:
```bash
cd curavani_frontend_internal
docker tag curavani-frontend:backup curavani-frontend:latest
make stop
docker run -d --name curavani-frontend-prod -p 80:80 curavani-frontend:latest
```

## Important Notes

### First Time Setup
1. Create all `.env` files
2. Set strong passwords in `.env.prod`
3. Make scripts executable: `chmod +x scripts/*.sh`
4. Set up cron for hourly backups
5. Run initial database migrations on production

### API Compatibility
- Frontend expects backend on ports 8011-8015
- Update `.env.production` if backend ports change
- Consider API versioning for breaking changes

### Zero-Downtime Frontend
- Users might need to clear cache after deployment
- Consider adding version number to UI
- Old frontend continues working during deployment

### Database Migrations
- Always test in development first
- Consider adding migration step to backend deploy script
- Keep migration files in version control

### Monitoring
- Check health endpoints regularly
- Monitor disk space for backups
- Set up alerts for failed cron jobs

## Advantages of Separated Deployment

1. **Deploy frontend frequently** without touching backend
2. **Different testing requirements** - frontend just needs build test
3. **Independent rollback** - frontend issues don't affect backend
4. **Simpler scripts** - each focused on one concern
5. **Better for teams** - frontend/backend devs work independently

## Future Enhancements

1. Add `deploy-all.sh` script at root level when needed
2. Add frontend version display in UI
3. Consider blue-green deployment for backend
4. Add automated frontend tests before deployment
5. Set up monitoring and alerting
