# Common Errors in the Therapy Matching Platform

## Kafka Connection Issues

### Error
```
Failed to connect to Kafka: NoBrokersAvailable
```

### Cause
Services start before Kafka is fully initialized.

### Solution
The `RobustKafkaProducer` handles this gracefully by queuing messages until Kafka is available. The error is expected and non-fatal.

### Best Practices
- Use `RobustKafkaProducer` for non-blocking initialization
- Configure proper health checks with `condition: service_healthy`
- Initial "Failed to connect" messages are normal

---

## Kafka Zookeeper Registration Conflict

### Error
```
org.apache.zookeeper.KeeperException$NodeExistsException: KeeperErrorCode = NodeExists
```

### Cause
Kafka cannot register with Zookeeper because a stale broker registration exists from a previous run.

### Solution
Restart only Kafka and Zookeeper containers (preserves database):
```bash
# Stop only Kafka and Zookeeper
docker-compose stop kafka zookeeper

# Remove only these containers (not volumes)
docker-compose rm -f kafka zookeeper

# Restart them fresh
docker-compose up -d kafka zookeeper
```

### Note
This is safe because:
- PostgreSQL data is in a named volume (`postgres_data`) which is preserved
- Kafka/Zookeeper only use container storage (no persistent volumes defined)

---

## PgBouncer Health Check Issues

### Error
```
dependency failed to start: container boona_mvp-pgbouncer-1 is unhealthy
```

### Solution
Use socket-based health checks instead of network-based checks.

---

## PostgreSQL "database does not exist" Error

### Error
```
FATAL: database "curavani" does not exist
```

### Cause
PostgreSQL utilities (`psql`, `pg_isready`, `pg_dump`) default to using the username as the database name when no database is explicitly specified. If your username is `curavani` but your database is `therapy_platform`, connection attempts without `-d` flag will fail.

### Common Locations
1. **Health checks** in docker-compose.yml
2. **Backup scripts** (pg_isready, pg_dump commands)
3. **PgBouncer health checks**
4. **Manual psql commands**

### Solution
Always explicitly specify the database name with `-d` flag:

```bash
# Incorrect (will try to connect to database with same name as user)
pg_isready -U curavani -h postgres
psql -U curavani -h postgres

# Correct
pg_isready -U curavani -h postgres -d therapy_platform
psql -U curavani -h postgres -d therapy_platform

# In scripts
PGPASSWORD="$DB_PASSWORD" pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME"
```

### Debugging Steps
1. Check all services one by one:
```bash
docker-compose up postgres -d
docker logs postgres | grep "database.*does not exist"
```

2. Common culprits:
- `postgres-backup` service watchdog and backup scripts
- PgBouncer health check commands
- Service initialization scripts

### Prevention
- Always use `-d $DB_NAME` in all PostgreSQL commands
- Set `PGDATABASE` environment variable as a fallback
- Use connection strings that include the database name

---

## Enum Value Mismatch in API Requests

### Error
```
ValueError: 'aktiv' is not a valid SearchStatus
```

### Cause
Sending incorrect enum values in API requests. The system uses German enum values.

### Correct Enum Values

```python
# SearchStatus
ACTIVE = "aktiv"
SUCCESSFUL = "erfolgreich"
PAUSED = "pausiert"
CANCELLED = "abgebrochen"

# PhoneCallStatus
SCHEDULED = "geplant"
COMPLETED = "abgeschlossen"
FAILED = "fehlgeschlagen"
CANCELED = "abgebrochen"

# ResponseType
FULL_ACCEPTANCE = "vollstaendige_annahme"
PARTIAL_ACCEPTANCE = "teilweise_annahme"
FULL_REJECTION = "vollstaendige_ablehnung"
NO_RESPONSE = "keine_antwort"
```

### Example API Request
```bash
# Correct
curl -X PUT http://localhost:8003/api/platzsuchen/1 \
  -H "Content-Type: application/json" \
  -d '{"status":"aktiv"}'
```

---

## Database Enum Value Mismatch

### Error
```
ERROR: invalid input value for enum searchstatus: "active"
```

### Solution
Always use enum `.value` property for database queries:

```python
# Correct for filtering
query.filter(Email.status == EmailStatus.SENT.value)

# Or cast the column
query.filter(cast(Email.status, String) == EmailStatus.SENT.value)

# For assignment, use enum directly
email.status = EmailStatus.DRAFT  # SQLAlchemy handles conversion
```

### Verify Enum Values
```sql
SELECT t.typname, e.enumlabel 
FROM pg_type t 
JOIN pg_enum e ON t.oid = e.enumtypid
ORDER BY t.typname, e.enumsortorder;
```

---

## Flask-RESTful Default Value Handling

### Error
```
null value in column "absender_email" violates not-null constraint
```

### Cause
RequestParser adds `None` for undefined arguments, which bypasses `.get()` defaults.

### Solution
Use the `or` operator for default values:

```python
# Correct (handles None values)
absender_email = args.get('absender_email') or smtp_settings['sender']

# Incorrect (only handles missing keys)
absender_email = args.get('absender_email', smtp_settings['sender'])
```

---

## Docker Import Path Issues

### Error
```
ModuleNotFoundError: No module named 'matching_service'
```

### Solutions

**Option 1**: Fix imports to match container structure
```python
# Change from:
from matching_service.algorithms.matcher import calculate_distance
# To:
from algorithms.matcher import calculate_distance
```

**Option 2**: Mount entire project in Docker
```yaml
volumes:
  - .:/app  # Instead of ./matching_service:/app
```

**Option 3**: Set PYTHONPATH
```dockerfile
ENV PYTHONPATH=$PYTHONPATH:/app
```

---

## Missing Dependencies

### Error
```
ModuleNotFoundError: No module named 'requests'
```

### Solution
1. Add to service's `requirements.txt`
2. Rebuild Docker image:
```bash
docker-compose build service-name
docker-compose up -d service-name
```

### Best Practices
- Update requirements.txt immediately when adding dependencies
- Use specific versions (e.g., `requests==2.31.0`)
- Separate dev dependencies in `requirements-dev.txt`