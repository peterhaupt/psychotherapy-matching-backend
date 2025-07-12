# Curavani Deployment Implementation Guide

## Overview

This guide documents the **three-environment setup** (Development, Test, Production) with complete separation and **independent deployment** for backend and frontend. All configuration has been externalized and environment-specific validation is implemented.

## ✅ Implementation Status Summary

### **IMPLEMENTED ✅**
- **Three-environment architecture** with complete isolation
- **Complete configuration externalization** (80+ environment variables)
- **All docker-compose files** (dev/test/prod) with proper service isolation  
- **Backend deployment scripts** (deploy.sh, rollback.sh)
- **Containerized database backups** with hourly/weekly retention
- **Comprehensive Makefile** with dev/test/prod commands
- **Alembic database migrations** for all environments
- **Test-first deployment** approach with mandatory test environment validation
- **Configuration validation** at startup for all services

### **TODO 🔄**
- **Frontend deployment implementation** (separate repository approach)

## Architecture Summary

- **Three separate environments**: Development, Test, Production with complete isolation
- **Independent deployment**: Deploy frontend and backend separately
- **No shared resources** between environments
- **Downtime**: Backend 30-60 seconds, Frontend zero downtime
- **Complete configuration externalization**: All hardcoded values removed
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
| React App | 3000 | 3001 | 80 |

## File Structure

```
curavani_backend/
├── docker-compose.dev.yml          ✅ IMPLEMENTED
├── docker-compose.test.yml         ✅ IMPLEMENTED  
├── docker-compose.prod.yml         ✅ IMPLEMENTED
├── .env.example                    ✅ IMPLEMENTED (80+ variables)
├── .env.dev                        ✅ CREATED
├── .env.test                       ✅ CREATED
├── .env.prod                       ✅ CREATED
├── Makefile                        ✅ IMPLEMENTED (full test environment support)
├── migrations/                     ✅ ALEMBIC MIGRATIONS
│   ├── alembic.ini
│   ├── env.py
│   └── versions/
├── docker/
│   └── postgres/
│       ├── Dockerfile              ✅ IMPLEMENTED (with cron backup)
│       └── backup-cron.sh          ✅ IMPLEMENTED
├── scripts/
│   ├── deploy.sh                   ✅ IMPLEMENTED (with migrations)
│   └── rollback.sh                 ✅ IMPLEMENTED
├── backups/
│   └── postgres/
│       ├── hourly/                 ✅ Auto-populated by cron
│       └── weekly/                 ✅ Auto-populated by cron
└── tests/
    ├── unit/                       ✅ Unit tests
    ├── integration/                ✅ Integration tests
    └── smoke/                      ✅ Smoke tests

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

# Part 1: Backend Setup ✅ IMPLEMENTED

## Environment Configuration

### Environment Files
Environment files have been created from the master template:
- `.env.dev` - Development configuration
- `.env.test` - Test configuration  
- `.env.prod` - Production configuration

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

### Configuration Validation
All services validate their required environment variables at startup:
- `config.validate("patient")` in patient_service/app.py
- `config.validate("therapist")` in therapist_service/app.py
- Service-specific validation for each microservice
- Clear error messages for missing variables

## Database Management

### Alembic Migrations
Database schema is managed through Alembic migrations located in the `migrations/` folder:

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

**Important**: The `init.sql` file has been removed. All database initialization is handled through Alembic migrations.

### Database Initialization
- Each environment has separate Docker volumes for data persistence
- First-time setup runs migrations automatically
- Existing databases are upgraded to the latest schema

## Automated Backups

### Containerized Backup System
Backups run automatically inside the PostgreSQL production container:
- **Hourly backups**: Every hour via cron
- **Weekly backups**: Sunday at midnight
- **Retention**: 7 days for hourly, 90 days for weekly
- **Location**: `./backups/postgres/` on the host machine

The backup system is implemented through:
- Custom PostgreSQL Docker image with cron (`docker/postgres/Dockerfile`)
- Backup script running inside container (`docker/postgres/backup-cron.sh`)
- Automatic volume mount to host filesystem

## Deployment Scripts

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

## Testing Strategy

### Test Environment Purpose
The test environment serves as a mandatory gate before production deployment:
- Complete isolation from development and production
- Full test suite execution (unit, integration, smoke)
- Database reset for each deployment
- Production-like configuration

### Test Execution
All tests run from the host machine:
```bash
# Run all tests
make test-all

# Run specific test suites
make test-unit
make test-integration
make test-smoke

# Run tests against specific environments
make test-unit-test       # Against test environment
make test-smoke-prod      # Against production
```

---

# Part 2: Deployment Workflow

## Development Workflow

### Backend Development
```bash
# Start development environment
make dev                    # Start all services
make logs-dev              # View logs
make migrate-dev           # Run migrations
make test-unit             # Run unit tests locally
make stop-dev              # Stop services
```

Development environment is used for:
- Manual testing
- Local development with hot-reload
- Debugging

## Test-First Deployment

### Deploy to Test Environment Only
```bash
make deploy-test
```

This command:
1. Builds test images
2. Starts test environment
3. Resets test database (complete drop and recreate)
4. Runs Alembic migrations
5. Verifies migration status
6. Runs ALL tests (unit, integration, smoke)
7. Reports success/failure

### Full Deployment (Test + Production)
```bash
make deploy
```

This command:
1. **First runs `deploy-test`** (all steps above)
2. **If all tests pass**, deploys to production:
   - Creates database backup
   - Builds and deploys production images
   - Runs Alembic migrations on production
   - Verifies production migration status
   - Runs smoke tests on production
   - Reports final status

**Important**: Production deployment is blocked if any test fails in the test environment.

## Environment Management

### Check Environment Status
```bash
# All environments
make status

# Individual environments
make status-prod
make health-check
make health-check-test
```

### Database Access
```bash
make db-dev                # Development database
make db-test               # Test database  
make db-prod               # Production database
```

### View Logs
```bash
make logs-dev              # Development logs
make logs-test             # Test logs
make logs-prod             # Production logs
```

## Backup and Recovery

### Automatic Backups
- Configured automatically in production PostgreSQL container
- No manual cron setup required on host
- Backups appear in `./backups/postgres/` directory

### Manual Operations
```bash
# List available backups
make list-backups

# Manual backup (rarely needed)
make backup

# Rollback to specific backup
make rollback TIMESTAMP=20240115_143022
```

---

# Part 3: Frontend Setup 🔄 TODO (Separate Repository)

The frontend is implemented in a separate repository `curavani_frontend_internal` with independent deployment. This remains to be implemented.

---

# Usage Guide

## First Time Setup

1. **Verify environment files exist**:
   - `.env.dev`
   - `.env.test`
   - `.env.prod`

2. **Update production passwords** in `.env.prod`

3. **Make scripts executable**:
   ```bash
   chmod +x scripts/*.sh
   ```

4. **Initialize databases**:
   ```bash
   make dev && make migrate-dev
   make test-start && make migrate-test
   ```

## Daily Development

```bash
# Start development
make dev

# Run tests during development
make test-unit
make test-integration

# Deploy to test environment for validation
make deploy-test
```

## Production Deployment

```bash
# Full deployment with automatic testing
make deploy

# Or deploy only to test (for validation)
make deploy-test
```

## Important Notes

### Security Considerations
- **Production passwords**: Use strong, unique passwords in `.env.prod`
- **Environment isolation**: Each environment has separate databases and networks
- **Backup security**: Backups contain sensitive data, secure appropriately
- **Configuration validation**: Startup validation prevents misconfigurations

### Migration Management
- Always test migrations in development first
- Use `make check-migrations-*` to verify status
- Migrations are forward-only (use rollback for reverting)

### Testing Philosophy
- **Development**: For manual testing and development
- **Test**: Automated gate for all deployments
- **Production**: Only receives tested code

### Performance and Monitoring
- **Health endpoints**: All services expose `/health`
- **Backup monitoring**: Check `./backups/postgres/` regularly
- **Service monitoring**: Use status commands frequently
- **Log monitoring**: Automated backup logs in container at `/var/log/backup.log`

## Advantages of This Approach

1. **Complete isolation**: Three environments never interfere
2. **Test-first deployment**: Production only receives tested code
3. **Zero manual backup management**: Containerized cron automation
4. **Consistent migration management**: Alembic across all environments
5. **Independent scaling**: Each environment can be sized differently
6. **Rollback safety**: Automatic backups before deployment
7. **Configuration consistency**: Same patterns everywhere

## Troubleshooting

### Common Issues

**Services not starting**: Check logs with `make logs-{env}`

**Migration failures**: 
- Verify database connectivity
- Check migration files in `migrations/versions/`
- Use `make check-migrations-{env}` to see current state

**Test failures blocking deployment**:
- Run tests individually to isolate issues
- Check test environment is fully up with `make health-check-test`

**Backup issues**: 
- Check container logs: `docker logs postgres-prod`
- Verify backup directory permissions
- Check disk space

---

*Implementation Status: Backend infrastructure complete, frontend deployment pending*