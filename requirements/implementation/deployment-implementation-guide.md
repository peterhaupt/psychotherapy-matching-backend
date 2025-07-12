# Curavani Deployment Implementation Guide - CONSOLIDATED

## Overview

This guide implements a **three-environment setup** (Development, Test, Production) with complete separation and **independent deployment** for backend and frontend. All configuration has been externalized and environment-specific validation is implemented.

## ✅ Implementation Status Summary

### **IMPLEMENTED ✅**
- **Three-environment architecture** with complete isolation
- **Complete configuration externalization** (80+ environment variables)
- **All docker-compose files** (dev/test/prod) with proper service isolation  
- **Backend deployment scripts** (deploy.sh, rollback.sh, backup-hourly.sh)
- **Configuration validation** at startup for all services
- **Database backup infrastructure** with hourly/weekly retention
- **Basic Makefile** with dev/prod commands

### **TODO 🔄**
- **Test environment commands** in Makefile (test-start, test-stop, etc.)
- **Actual production deployment** (currently only development is used)
- **Frontend deployment implementation** (separate repository approach)

## Architecture Summary

- **Three separate environments**: Development, Test, Production with complete isolation
- **Independent deployment**: Deploy frontend and backend separately
- **No shared resources** between environments
- **Downtime**: Backend 30-60 seconds, Frontend zero downtime
- **Complete configuration externalization**: All hardcoded values removed

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
| React App | 3000 | 3001 | 80 |

## File Structure ✅ IMPLEMENTED

```
curavani_backend/
├── docker-compose.dev.yml          ✅ IMPLEMENTED
├── docker-compose.test.yml         ✅ IMPLEMENTED  
├── docker-compose.prod.yml         ✅ IMPLEMENTED
├── .env.example                    ✅ IMPLEMENTED (80+ variables)
├── .env.dev                        🔄 TODO (copy from .env.example)
├── .env.test                       🔄 TODO (copy from .env.example)
├── .env.prod                       🔄 TODO (copy from .env.example)
├── Makefile                        ✅ IMPLEMENTED (needs test commands)
├── scripts/
│   ├── deploy.sh                   ✅ IMPLEMENTED
│   ├── rollback.sh                 ✅ IMPLEMENTED
│   └── backup-hourly.sh            ✅ IMPLEMENTED
└── backups/
    └── postgres/
        ├── hourly/                 ✅ IMPLEMENTED (structure)
        └── weekly/                 ✅ IMPLEMENTED (structure)

curavani_frontend_internal/         🔄 TODO (separate repository)
├── Dockerfile                      🔄 TODO
├── nginx.conf                      🔄 TODO
├── .env.development                🔄 TODO
├── .env.production                 🔄 TODO
├── Makefile                        🔄 TODO
└── scripts/
    └── deploy.sh                   🔄 TODO
```

---

# Part 1: Backend Setup ✅ MOSTLY IMPLEMENTED

## Environment Configuration ✅ IMPLEMENTED

### Master Environment Template
The `.env.example` file contains all 80+ environment variables needed across all services. Copy this file to create environment-specific configurations:

```bash
# Create environment files from master template
cp .env.example .env.dev     # Development configuration
cp .env.example .env.test    # Test configuration  
cp .env.example .env.prod    # Production configuration
```

### Key Environment Variables by Category

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

### Configuration Validation ✅ IMPLEMENTED
All services validate their required environment variables at startup:
- `config.validate("patient")` in patient_service/app.py
- `config.validate("therapist")` in therapist_service/app.py
- Service-specific validation for each microservice
- Clear error messages for missing variables

## Docker Compose Files ✅ IMPLEMENTED

### Development Environment
File: `docker-compose.dev.yml`
- Ports: 8001-8005
- Volume mounts for hot-reload development
- Development-specific configurations

### Test Environment  
File: `docker-compose.test.yml`
- Ports: 8011-8015
- Isolated test database and Kafka
- Test-specific configurations

### Production Environment
File: `docker-compose.prod.yml`
- Ports: 8021-8025
- No volume mounts for security
- Production-optimized configurations

## Deployment Scripts ✅ IMPLEMENTED

### Production Deployment Script
File: `scripts/deploy.sh`
- Automatic database backup before deployment
- Health checks for all services
- Smoke test execution
- Rollback information on failure

### Rollback Script
File: `scripts/rollback.sh`
- Database restoration from timestamped backups
- Service restart and health verification
- Available backup listing

### Backup Script
File: `scripts/backup-hourly.sh`
- Hourly database backups with compression
- Weekly backup creation (Sundays)
- Automatic cleanup (7 days hourly, 90 days weekly)
- Disk space monitoring

## Makefile ✅ PARTIALLY IMPLEMENTED

### Current Implementation
The `Makefile` includes dev/prod commands but needs test environment commands.

### 🔄 TODO: Add Test Environment Commands
Add these commands to the existing Makefile:

```makefile
# Test environment commands
test-start:
	docker-compose -f docker-compose.test.yml --env-file .env.test up -d

test-stop:
	docker-compose -f docker-compose.test.yml --env-file .env.test down

test-logs:
	docker-compose -f docker-compose.test.yml --env-file .env.test logs -f

test-build:
	docker-compose -f docker-compose.test.yml --env-file .env.test build

test-status:
	docker-compose -f docker-compose.test.yml --env-file .env.test ps

# Database access for test environment
db-test:
	docker exec -it postgres-test psql -U $(shell grep DB_USER .env.test | cut -d '=' -f2) $(shell grep DB_NAME .env.test | cut -d '=' -f2)

# Health checks for test environment
health-check-test:
	@echo "Checking test environment health endpoints..."
	@curl -s http://localhost:8011/health | jq '.' || echo "Patient service not responding"
	@curl -s http://localhost:8012/health | jq '.' || echo "Therapist service not responding"
	@curl -s http://localhost:8013/health | jq '.' || echo "Matching service not responding"
	@curl -s http://localhost:8014/health | jq '.' || echo "Communication service not responding"
	@curl -s http://localhost:8015/health | jq '.' || echo "Geocoding service not responding"

# Integration tests against test environment
integration-test:
	docker-compose -f docker-compose.test.yml --env-file .env.test exec patient_service-test pytest tests/integration -v
```

---

# Part 2: Frontend Setup 🔄 TODO (Separate Repository)

The frontend is implemented in a separate repository `curavani_frontend_internal` with independent deployment.

## Frontend Directory Structure 🔄 TODO

```
curavani_frontend_internal/
├── Dockerfile                      🔄 TODO
├── nginx.conf                      🔄 TODO
├── .env.development                🔄 TODO
├── .env.production                 🔄 TODO
├── Makefile                        🔄 TODO
└── scripts/
    └── deploy.sh                   🔄 TODO
```

## Production Build Configuration 🔄 TODO

### Dockerfile
Production-ready build with:
- Node.js 18 build stage
- Nginx serving stage  
- Environment variable injection for API endpoints
- Optimized for production deployment

### Nginx Configuration
- Compression and caching
- React routing support
- Security headers
- Performance optimizations

## Frontend Environment Files 🔄 TODO

### Development Environment
```bash
# Development API endpoints
REACT_APP_PATIENT_API=http://localhost:8001/api
REACT_APP_THERAPIST_API=http://localhost:8002/api
# ... other development endpoints
```

### Test Environment
```bash
# Test API endpoints  
REACT_APP_PATIENT_API=http://localhost:8011/api
REACT_APP_THERAPIST_API=http://localhost:8012/api
# ... other test endpoints
```

### Production Environment
```bash
# Production API endpoints
REACT_APP_PATIENT_API=http://localhost:8021/api
REACT_APP_THERAPIST_API=http://localhost:8022/api
# ... other production endpoints
```

## Frontend Deployment Script 🔄 TODO

The frontend deployment script should handle:
- Build validation
- Image backup and rollback capability
- Zero-downtime deployment
- Health checking

## Frontend Makefile 🔄 TODO

Frontend-specific commands for:
- Development server
- Production builds
- Docker operations
- Deployment and status checking

---

# Usage Guide

## Development Workflow ✅ IMPLEMENTED

### Backend Development
```bash
# Copy and configure environment
cp .env.example .env.dev
# Edit .env.dev with development values

# Start all backend services
make dev                    # Start development environment
make logs-dev              # View logs
make test                  # Run integration tests
make stop-dev              # Stop services
make status                # Show status of all environments
```

### Test Environment 🔄 TODO: Add Makefile Commands
```bash
# Copy and configure environment
cp .env.example .env.test
# Edit .env.test with test values

# Start test stack
make test-start            # 🔄 TODO: Add to Makefile
make test-logs             # 🔄 TODO: Add to Makefile
make integration-test      # 🔄 TODO: Add to Makefile
make test-stop             # 🔄 TODO: Add to Makefile
```

### Frontend Development 🔄 TODO (Separate Repository)
```bash
cd curavani_frontend_internal
make dev                   # Start React dev server (port 3000)
```

## Deployment Workflow

### Deploy Backend Only ✅ IMPLEMENTED
```bash
# Copy and configure production environment
cp .env.example .env.prod
# Edit .env.prod with production values (secure passwords!)

# Deploy with tests, backup, and health checks
make deploy                # Uses scripts/deploy.sh
```

### Deploy Frontend Only 🔄 TODO
```bash
cd curavani_frontend_internal
make deploy                # Build → Backup Image → Deploy → Health Check
```

### Check Environment Status
```bash
# Backend status across all environments
make status                # Shows dev, test, and prod status
make status-prod           # Production status only
make health-check          # Production health endpoints
make health-check-test     # 🔄 TODO: Test health endpoints

# Individual environment logs
make logs-dev              # Development logs
make test-logs             # 🔄 TODO: Test logs
make logs-prod             # Production logs
```

### Database Access
```bash
# Access databases for each environment
make db-dev                # Development database
make db-test               # 🔄 TODO: Test database  
make db-prod               # Production database
```

## Backup and Recovery ✅ IMPLEMENTED

### Automatic Backups
```bash
# Set up automatic hourly backups (add to cron)
0 * * * * /path/to/curavani_backend/scripts/backup-hourly.sh

# Manual backup
make backup

# List available backups
make list-backups
```

### Rollback Procedures
```bash
# Backend rollback to specific backup
make rollback TIMESTAMP=20240115_143022

# Frontend rollback (automatic on failed deployment)
# Manual frontend rollback available in separate repository
```

## Environment-Specific Deployment

### Development Environment ✅ IMPLEMENTED
```bash
# Start development with hot-reload
docker-compose -f docker-compose.dev.yml --env-file .env.dev up
```

### Test Environment ✅ IMPLEMENTED (Infrastructure)
```bash
# Start test environment
docker-compose -f docker-compose.test.yml --env-file .env.test up -d

# Run integration tests against test environment
pytest --env=test tests/integration/ -v
```

### Production Environment ✅ IMPLEMENTED
```bash
# Deploy to production with full pipeline
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

## Configuration Management ✅ IMPLEMENTED

### Environment Variable Management
1. **Master template**: `.env.example` contains all possible variables
2. **Service-specific validation**: Each service validates required variables at startup
3. **Environment isolation**: Separate configurations prevent cross-environment issues
4. **Security validation**: Production environment validates secure configurations

### Adding New Environment Variables
1. Add to `.env.example` with documentation
2. Update `shared/config/settings.py` with property and validation  
3. Add to service validation in `REQUIRED_BY_SERVICE` dictionary
4. Update docker-compose files to pass the variable
5. Test across all environments

## Important Notes

### First Time Setup
1. **Create environment files** from `.env.example`
2. **Set strong passwords** in `.env.prod`
3. **Make scripts executable**: `chmod +x scripts/*.sh`
4. **Set up cron** for hourly backups
5. **Run initial database migrations** on all environments

### Security Considerations
- **Production passwords**: Use strong, unique passwords in `.env.prod`
- **Environment isolation**: Each environment has separate databases and networks
- **Backup security**: Backups contain sensitive data, secure appropriately
- **Configuration validation**: Startup validation prevents misconfigurations

### API Compatibility
- **Frontend expectations**: Frontend expects backend on environment-specific ports
- **Cross-environment testing**: Use test environment for integration testing
- **Version compatibility**: Consider API versioning for breaking changes

### Performance and Monitoring
- **Health endpoints**: All services expose `/health` for monitoring
- **Backup monitoring**: Monitor disk space and backup success
- **Service monitoring**: Use `make status` and `make health-check` regularly

## Advantages of Three-Environment Approach

1. **Complete isolation**: Development, test, and production never interfere
2. **Safe testing**: Full integration testing in isolated test environment
3. **Production confidence**: Test environment mirrors production exactly
4. **Independent deployment**: Deploy services independently without affecting others
5. **Configuration consistency**: Same patterns across all environments
6. **Rollback safety**: Environment-specific backups and rollback procedures

## Next Steps

### Immediate TODOs 🔄
1. **Add test commands to Makefile** (test-start, test-stop, test-logs, etc.)
2. **Create environment files** (.env.dev, .env.test, .env.prod) from .env.example
3. **Set up cron job** for hourly backups in production
4. **Implement frontend deployment** in separate repository

### Future Enhancements
1. **Add monitoring and alerting** for production environment
2. **Implement blue-green deployment** for zero-downtime backend updates
3. **Add automated frontend testing** before deployment
4. **Set up log aggregation** across all environments
5. **Implement secrets management** for sensitive configuration

---

*Implementation Status: Backend infrastructure complete, test environment commands and frontend deployment pending*