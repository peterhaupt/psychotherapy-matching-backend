# Database Configuration

## Summary
This document details the database configuration for the Psychotherapy Matching Platform. It covers PostgreSQL setup, connection pooling with PgBouncer, schema management, database migrations with Alembic, and the centralized configuration approach.

## PostgreSQL Setup

### Docker Configuration
PostgreSQL is deployed as a Docker container via docker-compose.yml:
- PostgreSQL 16 (Alpine variant for smaller image size)
- Environment variables for credentials loaded from `.env` file
- Volume mapping for data persistence
- Health checks for service dependencies
- Port mapping for external access (optional)

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
The platform uses Bitnami's PgBouncer image for better cross-platform compatibility (including Apple Silicon):
- Configured in `docker-compose.yml`
- Connection pooling in session mode
- Support for up to 1000 client connections
- Default pool size of 25 connections

## Centralized Configuration

### Configuration Management
All database configuration is centralized in `shared/config/settings.py`:

```python
from shared.config import get_config

# Get configuration instance
config = get_config()

# Database connection URI
db_uri = config.get_database_uri()  # Uses PgBouncer by default
db_uri_direct = config.get_database_uri(use_pgbouncer=False)  # Direct connection
```

### Environment Variables
Database settings are configured via environment variables in `.env`:
- `DB_USER`: Database username
- `DB_PASSWORD`: Database password
- `DB_NAME`: Database name (default: therapy_platform)
- `DB_HOST`: PostgreSQL host (default: postgres)
- `DB_PORT`: PostgreSQL port (default: 5432)
- `PGBOUNCER_HOST`: PgBouncer host (default: pgbouncer)
- `PGBOUNCER_PORT`: PgBouncer port (default: 6432)

## Database Access Configuration

### SQLAlchemy Configuration
The shared SQLAlchemy configuration in `shared/utils/database.py` uses the centralized configuration:

```python
from shared.config import get_config

# Get configuration
config = get_config()

# Use the centralized database URI
DATABASE_URL = config.get_database_uri()

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
```

### Service Integration
Each service accesses the database through the shared configuration:

```python
# In service app.py files
from shared.config import get_config

config = get_config()
app.config["SQLALCHEMY_DATABASE_URI"] = config.get_database_uri()
```

## Database Migrations with Alembic

### Migration Environment Setup
The Alembic environment is configured in `migrations/alembic/env.py` to:
1. Import all models from services
2. Set the target metadata to the SQLAlchemy Base metadata
3. Enable autogeneration of migration scripts
4. Configure online and offline migration modes

### Migration Process

Key migration commands:
```bash
# Generate a new migration
cd migrations
alembic revision --autogenerate -m "description"

# Apply pending migrations
alembic upgrade head

# View migration history
alembic history

# Downgrade to previous version
alembic downgrade -1
```

### Migration Best Practices
1. Always review auto-generated migrations before applying
2. Test migrations in development before production
3. Include both upgrade and downgrade paths
4. Use descriptive migration messages

## Configuration for Different Environments

The centralized configuration supports multiple environments:

### Development (default)
```python
# Uses DevelopmentConfig with debug enabled
FLASK_ENV=development
```

### Production
```python
# Uses ProductionConfig with stricter settings
FLASK_ENV=production
# Validates required environment variables
# Enforces secure defaults
```

### Testing
```python
# Uses TestConfig with separate test database
FLASK_ENV=testing
# DB_NAME automatically becomes therapy_platform_test
```

## Troubleshooting

### Schema Issues
When migrations fail with "schema does not exist" errors:
1. Ensure the schema initialization script is correctly mounted
2. Verify schemas exist: `docker-compose exec postgres psql -U $DB_USER -d $DB_NAME -c "\dn"`
3. Recreate database volume if needed: `docker-compose down -v` (WARNING: deletes data)

### Connection Issues
If database connection errors occur:
1. Verify PgBouncer is running: `docker-compose ps pgbouncer`
2. Check PgBouncer logs: `docker-compose logs pgbouncer`
3. Test direct connection: `config.get_database_uri(use_pgbouncer=False)`
4. Ensure `.env` file has correct credentials

### PgBouncer Issues
For PgBouncer-specific problems:
1. Check if using Bitnami image (recommended for Apple Silicon)
2. Verify environment variables match between services
3. Test connection: `docker-compose exec postgres psql -h pgbouncer -p 6432 -U $DB_USER -d $DB_NAME`

## Best Practices

1. **Use Centralized Configuration**: Always use `shared.config` for database settings
2. **Environment Variables**: Never hardcode credentials; use `.env` file
3. **Connection Pooling**: Always connect through PgBouncer in production
4. **Schema Isolation**: Each service should only access its own schema
5. **Migration Testing**: Test all migrations in development first
6. **Health Checks**: Use Docker health checks for proper startup ordering