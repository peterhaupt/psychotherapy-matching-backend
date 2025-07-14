# Curavani Complete Deployment Implementation Guide

## Overview

This guide documents the **three-environment setup** (Development, Test, Production) with complete separation and **independent deployment** for backend and frontend. All configuration has been externalized and environment-specific validation is implemented.

## ✅ Implementation Status Summary

### **BACKEND: FULLY IMPLEMENTED ✅**
- **Three-environment architecture** with complete isolation
- **Complete configuration externalization** (80+ environment variables)
- **All docker-compose files** (dev/test/prod) with proper service isolation  
- **Backend deployment scripts** (deploy.sh, rollback.sh)
- **Containerized database backups** with hourly/weekly retention
- **Comprehensive Makefile** with dev/test/prod commands
- **Alembic database migrations** for all environments
- **Test-first deployment** approach with mandatory test environment validation
- **Configuration validation** at startup for all services

### **FRONTEND: IMPLEMENTATION READY 🔄**
- **Separate repository approach** (`curavani_frontend_internal`)
- **Docker-based deployment** for test/prod environments
- **Nginx serving** production builds
- **Complete network isolation** from backend
- **Environment-specific configuration** following React conventions

## Architecture Summary

- **Three separate environments**: Development, Test, Production with complete isolation
- **Independent deployment**: Frontend and backend deployed separately
- **No shared resources** between environments
- **Complete network isolation**: Frontend and backend use separate Docker networks
- **Communication**: Frontend (browser) → Backend (localhost ports)
- **Downtime**: Backend 30-60 seconds, Frontend 5-10 seconds
- **Database migrations**: Alembic-based migrations in `migrations/` folder
- **Automated backups**: Running inside PostgreSQL container with cron

## Port Mapping

| Service | Development | Test | Production |
|---------|------------|------|------------|
| **Backend Services** | | | |
| PostgreSQL | 5432 | 5433 | 5434 |
| PgBouncer | 6432 | 6433 | 6434 |
| Kafka | 9092 | 9093 | 9094 |
| Zookeeper | 2181 | 2182 | 2183 |
| Patient Service | 8001 | 8011 | 8021 |
| Therapist Service | 8002 | 8012 | 8022 |
| Matching Service | 8003 | 8013 | 8023 |
| Communication Service | 8004 | 8014 | 8024 |
| Geocoding Service | 8005 | 8015 | 8025 |
| **Frontend** | | | |
| React App | 3000 | 3001 | 3002 |

## File Structure

```
curavani_backend/                   ✅ FULLY IMPLEMENTED
├── docker-compose.dev.yml          ✅ IMPLEMENTED
├── docker-compose.test.yml         ✅ IMPLEMENTED  
├── docker-compose.prod.yml         ✅ IMPLEMENTED
├── .env.example                    ✅ IMPLEMENTED (80+ variables)
├── .env.dev                        ✅ CREATED
├── .env.test                       ✅ CREATED
├── .env.prod                       ✅ CREATED
├── Makefile                        ✅ IMPLEMENTED
├── migrations/                     ✅ ALEMBIC MIGRATIONS
│   ├── alembic.ini
│   ├── env.py
│   └── versions/
├── docker/
│   └── postgres/
│       ├── Dockerfile              ✅ IMPLEMENTED (with cron backup)
│       └── backup-cron.sh          ✅ IMPLEMENTED
├── scripts/
│   ├── deploy.sh                   ✅ IMPLEMENTED
│   └── rollback.sh                 ✅ IMPLEMENTED
├── backups/
│   └── postgres/
│       ├── hourly/                 ✅ Auto-populated by cron
│       └── weekly/                 ✅ Auto-populated by cron
└── tests/
    ├── unit/                       ✅ Unit tests
    ├── integration/                ✅ Integration tests
    └── smoke/                      ✅ Smoke tests

curavani_frontend_internal/         🔄 SEPARATE REPOSITORY
├── Dockerfile                      🔄 Multi-stage build
├── docker-compose.test.yml         🔄 Test environment
├── docker-compose.prod.yml         🔄 Production environment
├── nginx.conf                      🔄 Nginx configuration
├── .env.development                🔄 Dev config (React convention)
├── .env.test                       🔄 Test config
├── .env.production                 🔄 Prod config
├── Makefile                        🔄 Deployment commands
└── scripts/
    └── deploy.sh                   🔄 Frontend deployment
```

---

# Part 1: Backend Setup ✅ FULLY COMPLETED

## CORS Configuration Update Required

Before deploying the frontend, update CORS settings in backend environment files:

### Update Backend CORS Settings
```bash
# .env.dev
CORS_ALLOWED_ORIGINS=http://localhost:3000

# .env.test  
CORS_ALLOWED_ORIGINS=http://localhost:3001

# .env.prod
CORS_ALLOWED_ORIGINS=http://localhost:3002
```

After updating, restart the respective backend environment for changes to take effect.

## Backend Environment Configuration

### Environment Files
Environment files have been created from the master template:
- `.env.dev` - Development configuration
- `.env.test` - Test configuration  
- `.env.prod` - Production configuration

### Key Backend Variables by Category

**Database Configuration:**
- `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_HOST`, `DB_PORT`
- `DB_EXTERNAL_PORT`, `PGBOUNCER_EXTERNAL_PORT` (host-side ports)

**Service Ports (environment-specific):**
- Development: `PATIENT_SERVICE_PORT=8001` through `GEOCODING_SERVICE_PORT=8005`
- Test: `PATIENT_SERVICE_PORT=8011` through `GEOCODING_SERVICE_PORT=8015`
- Production: `PATIENT_SERVICE_PORT=8021` through `GEOCODING_SERVICE_PORT=8025`

**Service Configuration:**
- `SERVICE_ENV_SUFFIX` ("" for dev, "-test" for test, "-prod" for prod)
- All 80+ variables documented in `.env.example`

## Database Management

### Alembic Migrations
Database schema is managed through Alembic migrations:

```bash
# Run migrations for each environment
make migrate-dev       # Development
make migrate-test      # Test environment
make migrate-prod      # Production

# Check migration status
make check-migrations-dev
make check-migrations-test
make check-migrations-prod
```

## Automated Backups

### Containerized Backup System
Backups run automatically inside the PostgreSQL production container:
- **Hourly backups**: Every hour via cron
- **Weekly backups**: Sunday at midnight
- **Retention**: 7 days for hourly, 90 days for weekly
- **Location**: `./backups/postgres/` on the host machine

## Backend Deployment Scripts

### Production Deployment Script
File: `scripts/deploy.sh`
- Automatic database backup before deployment
- Runs Alembic migrations
- Health checks for all services
- Smoke test execution
- Rollback information on failure

### Rollback Script
File: `scripts/rollback.sh`
- Database restoration from timestamped backups
- Service restart and health verification
- Available backup listing

---

# Part 2: Frontend Setup 🔄 READY FOR IMPLEMENTATION

## Frontend Architecture

### Development Environment
- **No Docker**: Uses `npm start` directly on port 3000
- **Hot reload**: Development server with immediate updates
- **Mock data**: Can use `REACT_APP_USE_MOCK_DATA=true` for offline development

### Test/Production Environments
- **Docker containers**: Separate containers for test and prod
- **Nginx serving**: Optimized static file serving
- **Production builds**: `npm run build` creates optimized bundles
- **Complete isolation**: Separate Docker networks from backend

## Frontend Environment Configuration

### Environment Files (React Convention)
Create three environment files in the frontend repository:

#### .env.development
```bash
# Development Environment (port 3000)
REACT_APP_PATIENT_API=http://localhost:8001/api
REACT_APP_THERAPIST_API=http://localhost:8002/api
REACT_APP_MATCHING_API=http://localhost:8003/api
REACT_APP_COMMUNICATION_API=http://localhost:8004/api
REACT_APP_USE_MOCK_DATA=false
```

#### .env.test
```bash
# Test Environment (port 3001)
REACT_APP_PATIENT_API=http://localhost:8011/api
REACT_APP_THERAPIST_API=http://localhost:8012/api
REACT_APP_MATCHING_API=http://localhost:8013/api
REACT_APP_COMMUNICATION_API=http://localhost:8014/api
REACT_APP_USE_MOCK_DATA=false
```

#### .env.production
```bash
# Production Environment (port 3002)
REACT_APP_PATIENT_API=http://localhost:8021/api
REACT_APP_THERAPIST_API=http://localhost:8022/api
REACT_APP_MATCHING_API=http://localhost:8023/api
REACT_APP_COMMUNICATION_API=http://localhost:8024/api
REACT_APP_USE_MOCK_DATA=false
```

## Frontend Docker Configuration

### Dockerfile (Multi-stage Build)
```dockerfile
# Build stage
FROM node:18-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### docker-compose.test.yml
```yaml
name: curavani_frontend_test
services:
  frontend-test:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: frontend-test
    ports:
      - "3001:80"
    networks:
      - curavani_frontend_test

networks:
  curavani_frontend_test:
    name: curavani_frontend_test
    driver: bridge
```

### docker-compose.prod.yml
```yaml
name: curavani_frontend_prod
services:
  frontend-prod:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: frontend-prod
    ports:
      - "3002:80"
    networks:
      - curavani_frontend_prod

networks:
  curavani_frontend_prod:
    name: curavani_frontend_prod
    driver: bridge
```

### nginx.conf
```nginx
server {
    listen 80;
    server_name localhost;
    
    location / {
        root /usr/share/nginx/html;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;
    }
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

## Frontend Makefile

Create a Makefile that mirrors the backend structure:

```makefile
.PHONY: start-test start-prod stop-test stop-prod logs-test logs-prod build-test build-prod deploy-test deploy help

# Test environment commands
start-test:
	docker-compose -f docker-compose.test.yml up -d

stop-test:
	docker-compose -f docker-compose.test.yml down

logs-test:
	docker-compose -f docker-compose.test.yml logs -f

build-test:
	docker-compose -f docker-compose.test.yml build

# Production environment commands
start-prod:
	docker-compose -f docker-compose.prod.yml up -d

stop-prod:
	docker-compose -f docker-compose.prod.yml down

logs-prod:
	docker-compose -f docker-compose.prod.yml logs -f

build-prod:
	docker-compose -f docker-compose.prod.yml build

# Deployment commands
deploy-test:
	@echo "🚀 Deploying frontend to TEST environment..."
	$(MAKE) build-test
	$(MAKE) stop-test
	$(MAKE) start-test
	@echo "✅ Frontend test deployment complete!"
	@echo "Access at: http://localhost:3001"

deploy:
	@echo "🚀 Deploying frontend to PRODUCTION..."
	$(MAKE) build-prod
	$(MAKE) stop-prod  
	$(MAKE) start-prod
	@echo "✅ Frontend production deployment complete!"
	@echo "Access at: http://localhost:3002"

# Help
help:
	@echo "Frontend Makefile Commands:"
	@echo ""
	@echo "Test Environment:"
	@echo "  make start-test   - Start test environment"
	@echo "  make stop-test    - Stop test environment"
	@echo "  make logs-test    - View test logs"
	@echo "  make build-test   - Build test image"
	@echo "  make deploy-test  - Deploy to test"
	@echo ""
	@echo "Production:"
	@echo "  make start-prod   - Start production"
	@echo "  make stop-prod    - Stop production"
	@echo "  make logs-prod    - View production logs"
	@echo "  make build-prod   - Build production image"
	@echo "  make deploy       - Deploy to production"
```

---

# Part 3: Deployment Workflow

## Complete System Architecture

### Network Isolation
- Backend networks: `curavani_backend_dev`, `curavani_backend_test`, `curavani_backend_prod`
- Frontend networks: `curavani_frontend_test`, `curavani_frontend_prod`
- No cross-network communication needed (browser handles API calls)

### Communication Flow
1. User accesses frontend (localhost:3000/3001/3002)
2. Browser loads React application from frontend container
3. React app makes API calls directly to backend ports
4. Backend CORS allows requests from respective frontend URLs

## Development Workflow

### Backend Development
```bash
# In curavani_backend/
make dev                    # Start all backend services
make logs-dev              # View logs
make migrate-dev           # Run migrations
make stop-dev              # Stop services
```

### Frontend Development
```bash
# In curavani_frontend_internal/
npm start                  # Runs on http://localhost:3000
```

## Test Deployment

### Backend Test Deployment
```bash
# In curavani_backend/
make deploy-test           # Full test deployment with tests
```

### Frontend Test Deployment
```bash
# In curavani_frontend_internal/
make deploy-test           # Deploy frontend to test
```

Access test system at:
- Frontend: http://localhost:3001
- Backend APIs: http://localhost:8011-8015

## Production Deployment

### Backend Production Deployment
```bash
# In curavani_backend/
make deploy                # Test + Production deployment
```

### Frontend Production Deployment
```bash
# In curavani_frontend_internal/
make deploy                # Deploy frontend to production
```

Access production system at:
- Frontend: http://localhost:3002
- Backend APIs: http://localhost:8021-8025

## First Time Setup Guide

### 1. Backend Setup (Already Complete)
```bash
cd curavani_backend
# Verify environment files exist
ls -la .env.*
# Update CORS settings in all .env files
# Start development
make dev
```

### 2. Frontend Setup
```bash
cd curavani_frontend_internal

# Create environment files
cp .env.example .env.development
cp .env.example .env.test  
cp .env.example .env.production

# Update API URLs in each file according to the port mappings

# Create Docker files
# - Dockerfile
# - docker-compose.test.yml
# - docker-compose.prod.yml
# - nginx.conf
# - Makefile

# Test the setup
make deploy-test
```

### 3. Verify Complete System
1. Start backend test: `cd curavani_backend && make start-test`
2. Deploy frontend test: `cd curavani_frontend_internal && make deploy-test`
3. Access http://localhost:3001
4. Verify API calls work (check browser network tab)

## Docker Desktop Organization

After deployment, Docker Desktop will show:
```
▼ curavani_backend_dev
  - postgres
  - pgbouncer
  - kafka
  - patient_service
  - therapist_service
  - matching_service
  - communication_service
  - geocoding_service

▼ curavani_backend_test
  - postgres-test
  - pgbouncer-test
  - kafka-test
  - patient_service-test
  - therapist_service-test
  - matching_service-test
  - communication_service-test
  - geocoding_service-test

▼ curavani_backend_prod
  - postgres-prod
  - pgbouncer-prod
  - kafka-prod
  - patient_service-prod
  - therapist_service-prod
  - matching_service-prod
  - communication_service-prod
  - geocoding_service-prod

▼ curavani_frontend_test
  - frontend-test

▼ curavani_frontend_prod
  - frontend-prod
```

## Important Notes

### Security Considerations
- **Environment files**: Never commit `.env.*` files to version control
- **CORS configuration**: Only allow specific frontend URLs
- **Network isolation**: Frontend and backend on separate networks
- **Production builds**: Always use optimized builds for test/prod

### Performance
- **Frontend caching**: Nginx serves static files efficiently
- **Browser caching**: Configure cache headers in nginx.conf
- **API calls**: All happen directly from browser to backend

### Troubleshooting

**Frontend not connecting to backend:**
1. Check CORS settings in backend `.env` files
2. Verify backend services are running
3. Check browser console for CORS errors
4. Ensure correct API URLs in frontend `.env` files

**Container build issues:**
1. Clear Docker cache: `docker system prune`
2. Check Node version compatibility
3. Verify all files are present

**Port conflicts:**
1. Check if ports are already in use
2. Use `lsof -i :PORT` to find conflicting processes
3. Adjust port mappings if needed

## Summary

### What's Implemented
- ✅ Complete backend three-environment setup
- ✅ Backend automated testing and deployment
- ✅ Backend database migrations and backups
- ✅ Frontend architecture design
- ✅ Frontend deployment configuration

### What's Ready for Implementation
- 🔄 Frontend Docker setup (Dockerfile, docker-compose files)
- 🔄 Frontend environment configuration
- 🔄 Frontend deployment scripts
- 🔄 CORS updates in backend

### Key Benefits
- Complete isolation between environments
- Consistent deployment approach for frontend and backend
- Simple single-user local deployment
- Clear organization in Docker Desktop
- Easy rollback capabilities

---

*Implementation Status: Backend fully completed, Frontend ready for implementation with all configurations defined*