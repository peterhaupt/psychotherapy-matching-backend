# Deployment and Operations

## Summary
Complete deployment infrastructure with three isolated environments (Development, Test, Production) and comprehensive operational procedures including automated backups, migrations, and deployment workflows.

## Three-Environment Architecture

### Environment Isolation
Each environment is completely isolated with:
- Separate Docker networks
- Unique container names and ports
- Independent databases and volumes
- Environment-specific configuration files

### Port Mapping

| Service | Development | Test | Production |
|---------|------------|------|------------|
| **Infrastructure** | | | |
| PostgreSQL | 5432 | 5433 | 5434 |
| PgBouncer | 6432 | 6433 | 6434 |
| Kafka | 9092 | 9093 | 9094 |
| Zookeeper | 2181 | 2182 | 2183 |
| **Microservices** | | | |
| Patient Service | 8001 | 8011 | 8021 |
| Therapist Service | 8002 | 8012 | 8022 |
| Matching Service | 8003 | 8013 | 8023 |
| Communication Service | 8004 | 8014 | 8024 |
| Geocoding Service | 8005 | 8015 | 8025 |

### File Structure
```
curavani_backend/
├── docker-compose.dev.yml      # Development environment
├── docker-compose.test.yml     # Test environment
├── docker-compose.prod.yml     # Production environment
├── .env.dev                    # Development configuration
├── .env.test                   # Test configuration
├── .env.prod                   # Production configuration
├── Makefile                    # Deployment automation
├── migrations/                 # Database migrations
│   ├── alembic.ini
│   ├── env.py
│   └── versions/
├── docker/
│   └── postgres/
│       ├── Dockerfile          # PostgreSQL with backup cron
│       └── backup-cron.sh      # Automated backup script
├── scripts/
│   ├── deploy.sh               # Production deployment
│   └── rollback.sh             # Rollback procedure
└── backups/
    └── postgres/
        ├── manual/             # On-demand backups
        ├── hourly/             # Automated hourly backups
        └── weekly/             # Automated weekly backups
```

## Deployment Workflows

### Test-First Deployment Approach
Production deployments always go through test environment first:

```bash
# 1. Deploy to test environment
make deploy-test

# 2. If tests pass, deploy to production
make deploy
```

### Backend Deployment Process
The deployment script (`scripts/deploy.sh`) performs:
1. Build new Docker images
2. Stop application services (keeps databases running)
3. Start updated services
4. Run database migrations
5. Execute health checks

**Downtime**: 30-60 seconds (only application services restart)

### Key Deployment Commands
- `make dev` - Start development environment
- `make deploy-test` - Deploy to test environment
- `make deploy` - Full deployment (test + production)
- `make rollback TIMESTAMP=xxx` - Rollback to specific backup
- `make status` - View all environment statuses
- `make health-check-[dev|test|prod]` - Check service health

## Database Operations

### Migrations
Alembic manages database schema changes:
- `make migrate-dev` - Run migrations in development
- `make migrate-test` - Run migrations in test
- `make migrate-prod` - Run migrations in production
- `make check-migrations-[env]` - Verify migration status

### Backup and Restore

#### Automated Backups
PostgreSQL containers run cron jobs for automatic backups:
- **Hourly**: Every hour at :00 (retained for 7 days)
- **Weekly**: Sundays at 00:00 (retained for 90 days)
- **Manual**: On-demand via `make backup-prod`

#### Backup Commands
```bash
# Create manual backup
make backup-prod

# List all backups
make list-backups

# Verify backup integrity
make backup-verify-prod BACKUP=20240115_143022

# Restore operations
make restore-prod BACKUP=20240115_143022  # Production (requires confirmation)
make restore-dev BACKUP=20240115_143022   # Development from production
make restore-test BACKUP=20240115_143022  # Test from production

# Test restore process
make test-restore-test
```

#### Restore Process
1. Verifies backup exists
2. Creates safety backup of current state
3. Stops application services
4. Drops and recreates database
5. Restores from backup
6. Runs missing migrations
7. Restarts services and checks health

## Docker Desktop Organization
After deployment, containers are organized by environment:
```
▼ curavani_backend_dev
  - postgres, pgbouncer, kafka, zookeeper
  - patient_service-dev, therapist_service-dev
  - matching_service-dev, communication_service-dev
  - geocoding_service-dev

▼ curavani_backend_test
  - postgres-test, pgbouncer-test, kafka-test, zookeeper-test
  - patient_service-test, therapist_service-test
  - matching_service-test, communication_service-test
  - geocoding_service-test

▼ curavani_backend_prod
  - postgres-prod, pgbouncer-prod, kafka-prod, zookeeper-prod
  - patient_service-prod, therapist_service-prod
  - matching_service-prod, communication_service-prod
  - geocoding_service-prod
```

## Monitoring and Health Checks

### Health Check Endpoints
Each service exposes `/health` endpoint with:
- Service status
- Database connectivity
- Kafka connectivity
- Version information

### Monitoring Commands
- `make status` - All environments overview
- `make health-check` - Production health check
- `make logs-[dev|test|prod]` - View environment logs
- `make check-db-[dev|test|prod]` - Verify database exists

## Testing Infrastructure

### Test Types
- **Unit Tests**: Service-specific logic testing
- **Integration Tests**: Cross-service communication testing
- **Smoke Tests**: Basic functionality verification

### Test Commands by Environment
```bash
# Development (ports 8001-8005)
make test-unit-dev
make test-integration-dev
make test-smoke-dev
make test-all-dev

# Test Environment (ports 8011-8015)
make test-unit-test
make test-integration-test
make test-smoke-test
make test-all-test

# Production (ports 8021-8025)
make test-smoke-prod
```

## Configuration Management

### Environment Variables
Over 80 environment variables configured per environment:
- Database connections (with PgBouncer)
- Service ports and URLs
- Kafka configuration
- SMTP settings
- API keys and secrets
- Feature flags

### Configuration Validation
Services validate required configuration at startup using `shared.config`.

### CORS Configuration
Each environment configured with appropriate frontend URLs:
- Development: `http://localhost:3000`
- Test: `http://localhost:3001`
- Production: `http://localhost:3002`

## Issues Encountered and Resolved

### 1. Kafka Connection Issues
**Problem**: Services starting before Kafka fully initialized.
**Solution**: Implemented `RobustKafkaProducer` for graceful handling of connection failures.

### 2. Database Creation Timing
**Problem**: Services attempting to connect before database exists.
**Solution**: Added `ensure-db-[env]` commands in Makefile startup sequence.

### 3. Migration Failures
**Problem**: Migrations failing due to cross-service dependencies.
**Solution**: Proper service startup ordering and health checks.

### 4. Backup Restoration
**Problem**: Services attempting to connect during restore.
**Solution**: Stop application services during restore process.

## Best Practices

1. **Always test in test environment** before production deployment
2. **Create manual backup** before major changes
3. **Monitor logs** during deployment for issues
4. **Verify health checks** after deployment
5. **Use Makefile commands** for consistency
6. **Document configuration changes** in `.env.example`
7. **Test restore process** regularly to ensure backups work