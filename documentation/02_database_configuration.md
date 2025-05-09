# Database Configuration

## Summary
This document details the database configuration for the Psychotherapy Matching Platform. It covers PostgreSQL setup, connection pooling with PgBouncer, schema management, and database migrations with Alembic.

## PostgreSQL Setup

### Docker Configuration
PostgreSQL is deployed as a Docker container via docker-compose.yml. See the configuration in the project's docker-compose.yml file, which sets up:
- PostgreSQL 14 database
- Environment variables for credentials
- Volume mapping for data persistence
- Port mapping for external access

### Schema Initialization
Service-specific schemas are created using an initialization script at `docker/postgres/init.sql`. This script creates separate schemas for each microservice to maintain proper data isolation while using a single database instance.

## Connection Pooling with PgBouncer

### Why Connection Pooling?
PgBouncer is implemented to:
- Reduce connection overhead to the database
- Manage connection limits effectively
- Improve performance under concurrent load
- Allow for more efficient resource utilization

### Implementation
PgBouncer is configured in docker-compose.yml and uses configuration files:
- `pgbouncer.ini` located at `docker/pgbouncer/pgbouncer.ini`
- `userlist.txt` located at `docker/pgbouncer/userlist.txt`

## Database Access Configuration

### SQLAlchemy Configuration
A shared SQLAlchemy configuration is provided in `shared/utils/database.py`. This shared configuration ensures consistent database access patterns across all services, with:
- Connection string pointing to PgBouncer (port 6432) rather than direct PostgreSQL connection
- Session management utility functions
- Shared Base class for declarative models

## Database Migrations with Alembic

### Migration Environment Setup
The Alembic environment is configured in `migrations/alembic/env.py` to:
1. Import all models from services
2. Set the target metadata to the SQLAlchemy Base metadata
3. Enable autogeneration of migration scripts
4. Configure online and offline migration modes

### Migration Process

Key migration commands:
```
# Generate a new migration
cd migrations
alembic revision --autogenerate -m "description"

# Apply pending migrations
alembic upgrade head
```

## Troubleshooting

### Schema Issues
When migrations fail with "schema does not exist" errors, ensure that:
1. The schema initialization script is correctly mounted
2. The database volume is recreated if needed
3. The search path in the init script includes all required schemas

### Connection Issues
If database connection errors occur, verify:
1. PgBouncer is running and correctly configured
2. Connection URLs use the PgBouncer port (6432) not the direct PostgreSQL port
3. Credentials in all configuration files match