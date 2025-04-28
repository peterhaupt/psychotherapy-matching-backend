# Database Configuration

## Summary
This document details the database configuration for the Psychotherapy Matching Platform. It covers PostgreSQL setup, connection pooling with PgBouncer, schema management, and database migrations with Alembic.

## PostgreSQL Setup

### Docker Configuration
PostgreSQL is deployed as a Docker container via docker-compose.yml:

```yaml
services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_USER: boona
      POSTGRES_PASSWORD: boona_password
      POSTGRES_DB: therapy_platform
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./docker/postgres:/docker-entrypoint-initdb.d

volumes:
  postgres-data:
```

### Schema Initialization
Service-specific schemas are created using an initialization script at `docker/postgres/init.sql`:

```sql
-- Create schemas for each service
CREATE SCHEMA IF NOT EXISTS patient_service;
CREATE SCHEMA IF NOT EXISTS therapist_service;
CREATE SCHEMA IF NOT EXISTS matching_service;
CREATE SCHEMA IF NOT EXISTS communication_service;
CREATE SCHEMA IF NOT EXISTS geocoding_service;
CREATE SCHEMA IF NOT EXISTS scraping_service;

-- Set search path
SET search_path TO patient_service, public;
```

## Connection Pooling with PgBouncer

PgBouncer is used for database connection pooling to improve performance and reduce connection overhead.

### Docker Configuration
```yaml
pgbouncer:
  image: edoburu/pgbouncer:latest
  depends_on:
    - postgres
  ports:
    - "6432:6432"
  volumes:
    - ./docker/pgbouncer/pgbouncer.ini:/etc/pgbouncer/pgbouncer.ini
    - ./docker/pgbouncer/userlist.txt:/etc/pgbouncer/userlist.txt
  restart: unless-stopped
```

### PgBouncer Configuration
The `pgbouncer.ini` configuration file:

```ini
[databases]
therapy_platform = host=postgres dbname=therapy_platform user=boona password=boona_password

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
logfile = /var/log/pgbouncer/pgbouncer.log
pidfile = /var/run/pgbouncer/pgbouncer.pid
admin_users = boona
```

The `userlist.txt` file contains authentication information:
```
"boona" "boona_password"
```

## Database Access Configuration

### SQLAlchemy Configuration
A shared SQLAlchemy configuration is provided in `shared/utils/database.py`:

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = \
    "postgresql://boona:boona_password@pgbouncer:6432/therapy_platform"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

This configuration is used by all services to maintain a consistent database access pattern.

## Database Migrations with Alembic

### Alembic Configuration
The platform uses Alembic for database schema migrations. The configuration is in `migrations/alembic.ini`:

```ini
[alembic]
script_location = alembic
prepend_sys_path = .
sqlalchemy.url = postgresql://boona:boona_password@localhost:6432/therapy_platform
```

### Migration Environment Setup
The Alembic environment is configured in `migrations/alembic/env.py` to:
1. Import all models from services
2. Set the target metadata to the SQLAlchemy Base metadata
3. Enable autogeneration of migration scripts
4. Configure online and offline migration modes

### Initial Migration
The first migration creates the patient table and includes:
- All required fields from the specifications
- Proper data types and constraints
- Schema association to the patient_service schema
- Primary key and indexes

### Migration Process

To generate a new migration:
```bash
cd migrations
alembic revision --autogenerate -m "description"
```

To apply pending migrations:
```bash
alembic upgrade head
```

## Troubleshooting

### Schema Issues
When migrations fail with "schema does not exist" errors, ensure that:
1. The schema initialization script is correctly mounted
2. The database volume is recreated if needed:
   ```bash
   docker-compose down -v
   docker-compose up -d
   ```
3. The search path in the init script includes all required schemas

### Connection Issues
If database connection errors occur, verify:
1. PgBouncer is running and correctly configured
2. Connection URLs use the PgBouncer port (6432) not the direct PostgreSQL port
3. Credentials in all configuration files match