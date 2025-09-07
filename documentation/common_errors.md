# Common Errors in the Therapy Matching Platform

## Service Unavailability During Cascade Operations

### Error
```
Cannot delete patient: Matching service unavailable: HTTPConnectionPool(host='matching-service', port=8003): Max retries exceeded
Cannot block therapist: Matching service error: 503 Service Unavailable
```

### Cause
Dependent service is down or unreachable during a cascade operation. The system blocks the operation to maintain data consistency.

### Solution
1. **Verify service health**:
```bash
make health-check-dev  # or -test/-prod
docker-compose ps
```

2. **Restart affected service**:
```bash
docker-compose restart matching_service-dev
```

3. **Check service logs**:
```bash
docker-compose logs matching_service-dev
```

4. **Retry operation** after service is back online

### Prevention
- Monitor service health regularly
- Implement proper health checks in Docker Compose
- Use retry logic with exponential backoff
- Consider implementing circuit breakers for repeated failures

---

## Cross-Service API Timeout

### Error
```
ReadTimeout: HTTPConnectionPool(host='patient-service', port=8001): Read timed out. (read timeout=10)
```

### Cause
API call between services takes longer than configured timeout, often during cascade operations or when a service is under heavy load.

### Solution
1. **Increase timeout in shared.api.retry_client**:
```python
# Adjust timeout parameter
RetryAPIClient.call_with_retry(
    method="POST",
    url=url,
    json=data,
    timeout=30  # Increase from default 10 seconds
)
```

2. **Optimize the slow operation**:
- Add database indexes
- Reduce cascade operation complexity
- Implement pagination for large datasets

### Prevention
- Profile slow API endpoints
- Implement proper database indexing
- Use connection pooling (PgBouncer)
- Monitor API response times

---

## Cascade Operation Rollback

### Error
```
Database error: ROLLBACK; nested exception is psycopg2.errors.InFailedSqlTransaction
```

### Cause
A cascade operation partially succeeded but failed midway, leaving the database transaction in an inconsistent state.

### Solution
1. **Ensure proper transaction management**:
```python
db = SessionLocal()
try:
    # Cascade operations
    db.commit()
except Exception as e:
    db.rollback()
    raise
finally:
    db.close()
```

2. **Verify all cascade operations are idempotent**

3. **Check for database locks**:
```sql
SELECT * FROM pg_locks WHERE NOT granted;
```

### Prevention
- Use database transactions for all cascade operations
- Implement proper rollback handling
- Make operations idempotent where possible
- Add retry logic for transient failures

---

## Object Storage Connection Issues

### Error
```
Container 'dev' not found
SwiftService error: Authentication failed
ConnectionError: Unable to connect to Swift storage
```

### Cause
Issues connecting to Infomaniak Object Storage containers, usually due to authentication problems or incorrect environment configuration.

### Solution
1. **Verify Swift configuration**:
```bash
# Check environment variables
echo $SWIFT_AUTH_URL
echo $SWIFT_USERNAME
echo $SWIFT_PASSWORD
echo $SWIFT_CONTAINER_NAME
```

2. **Test Swift connection**:
```python
from swiftclient import service
swift_service = service.SwiftService(options={
    'auth_version': '3',
    'auth': auth_url,
    'user': username,
    'key': password,
    'tenant_name': tenant_name
})
containers = list(swift_service.list())
```

3. **Verify container exists and FLASK_ENV setting**:
```bash
# Ensure container name matches environment
# dev/test/prod containers should exist
```

### Prevention
- Regular authentication token refresh
- Monitor Swift service availability
- Implement proper error handling with retries
- Use health checks for Swift connectivity

---

## HMAC Verification Failures

### Error
```
HMAC verification failed: Invalid signature
Signature mismatch between PHP and Python
HMAC authentication error: Expected signature does not match
```

### Cause
HMAC signature verification fails when the secret keys don't match between PHP scraper and Python services, or when the signature generation algorithm differs.

### Solution
1. **Check HMAC_SECRET_KEY environment variable consistency**:
```bash
# Verify same secret in both PHP and Python environments
echo $HMAC_SECRET_KEY
```

2. **Verify signature generation algorithm**:
```python
# Python side - ensure same algorithm as PHP
import hmac
import hashlib

def verify_signature(data, signature, secret):
    expected = hmac.new(
        secret.encode('utf-8'),
        data.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

3. **Debug signature generation**:
```bash
# Log the data being signed and generated signature
# Compare with PHP output
```

### Prevention
- Use consistent HMAC algorithms across all services
- Store HMAC secrets in secure environment variables
- Implement signature verification in all data import endpoints
- Add comprehensive logging for signature verification

---

## Test Contamination from Module-Level Mocking

### Error
```
ModuleNotFoundError: No module named 'google.cloud.storage'
AttributeError: 'MagicMock' object has no attribute 'adapters'
ImportError: cannot import name 'Client' from 'unittest.mock'
```

### Symptoms
- Tests pass when run individually but fail when run together
- Different test results based on test execution order
- Import errors that don't make sense given your imports
- MagicMock objects appearing where real modules should be

### Cause
Module-level `sys.modules` mocking contaminates the global Python interpreter state:

```python
# BAD: This runs during test collection and affects ALL subsequent tests
import sys
from unittest.mock import MagicMock

sys.modules['requests'] = MagicMock()  # ❌ Pollutes global state
sys.modules['models'] = MagicMock()     # ❌ Persists across tests

from patient_service.api.patients import some_function  # Now imports with mocked deps
```

**Why this happens:**
1. Pytest runs all tests in a single Python process
2. During test collection, pytest imports ALL test files
3. Module-level code executes during import
4. `sys.modules` is global to the entire process
5. Once polluted, it affects all subsequent test files

### Example Timeline
```
1. Pytest collects test_payment_workflow.py
   → Executes: sys.modules['requests'] = MagicMock()
   → Now 'requests' is broken for the entire test run

2. Pytest collects test_gcs_file_import.py
   → Tries to: from google.cloud import storage
   → storage needs real 'requests.adapters'
   → But gets MagicMock instead → FAILS
```

### Solution: Fixture-Based Mocking

Create a `tests/unit/conftest.py` file with proper fixture-based mocking:

```python
# tests/unit/conftest.py
import pytest
import sys
from unittest.mock import MagicMock

@pytest.fixture(autouse=True, scope="function")
def mock_all_dependencies(monkeypatch):
    """Mock all dependencies with automatic cleanup."""
    
    # Mock modules using monkeypatch
    modules_to_mock = [
        'models', 'models.patient', 'shared', 'shared.utils',
        'flask', 'sqlalchemy', 'requests', # etc...
    ]
    
    for module_name in modules_to_mock:
        monkeypatch.setitem(sys.modules, module_name, MagicMock())
    
    # Set up specific mocks
    mock_config = MagicMock()
    mock_config.get_service_url = MagicMock(return_value="http://test-service")
    sys.modules['shared.config'].get_config = MagicMock(return_value=mock_config)
    
    # ... other mock setups ...
    
    yield  # Test runs here
    
    # Automatic cleanup by monkeypatch!
```

Then refactor test files to:
1. **Remove** all module-level `sys.modules` mocking
2. **Move** imports inside test methods:

```python
# BEFORE (BAD):
import sys
sys.modules['models'] = MagicMock()  # ❌ Module level
from patient_service.api.patients import validate_symptoms  # ❌ Module level

class TestSymptoms:
    def test_validation(self):
        validate_symptoms(["Depression"])

# AFTER (GOOD):
class TestSymptoms:
    def test_validation(self):
        # Import AFTER fixtures have set up mocks ✅
        from patient_service.api.patients import validate_symptoms
        validate_symptoms(["Depression"])
```

### Benefits of This Approach
- **Test Isolation**: Each test gets a clean `sys.modules` state
- **Automatic Cleanup**: `monkeypatch` restores original state after each test
- **No Contamination**: Tests can run in any order without issues
- **Pytest Best Practice**: Follows recommended patterns for test fixtures

### Migration Steps
1. Create `tests/unit/conftest.py` with the fixture
2. Remove module-level mocking from each test file
3. Move production code imports inside test methods
4. Run tests to verify isolation

### Alternative Quick Fixes (Not Recommended)
1. **Process Isolation**: Run each test in separate process
   ```bash
   pytest --forked  # Requires pytest-forked
   ```
   ⚠️ Slower, doesn't fix root cause

2. **Run Tests Individually**: Script to run each test file separately
   ```bash
   for test in tests/unit/test_*.py; do
       pytest "$test"
   done
   ```
   ⚠️ Hides the problem, CI/CD complexity

### Prevention
- Never mock `sys.modules` at module level
- Always use pytest fixtures for mocking
- Consider dependency injection in production code to reduce mocking needs
- Use `pytest-mock` or similar tools that provide proper cleanup

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

## PostgreSQL Client Version Mismatch in Backup Container

### Error
```
pg_dump: error: server version: 16.6; pg_dump version: 15.8
pg_dump: error: aborting because of server version mismatch
```

### Cause
The backup container is using a different version of PostgreSQL client tools than the main PostgreSQL server. The Alpine Linux `postgresql-client` package installs an older version (15.x) while the main PostgreSQL container runs version 16.x.

### Solution
Update the backup container Dockerfile to use PostgreSQL 16 client tools:

```dockerfile
FROM alpine:latest

# Install PostgreSQL 16 client from edge repository
RUN apk add --no-cache \
    curl \
    && echo "http://dl-cdn.alpinelinux.org/alpine/edge/main" >> /etc/apk/repositories \
    && apk add --no-cache postgresql16-client \
    && ln -s /usr/bin/psql16 /usr/bin/psql \
    && ln -s /usr/bin/pg_dump16 /usr/bin/pg_dump \
    && ln -s /usr/bin/pg_restore16 /usr/bin/pg_restore \
    && ln -s /usr/bin/pg_isready16 /usr/bin/pg_isready

COPY backup.sh /backup.sh
RUN chmod +x /backup.sh

CMD ["/backup.sh"]
```

### Rebuild Process
```bash
# Stop the current backup container
docker-compose -f docker-compose.dev.yml stop postgres-backup

# Rebuild with the new Dockerfile
docker-compose -f docker-compose.dev.yml build postgres-backup

# Start it back up
docker-compose -f docker-compose.dev.yml up -d postgres-backup

# Verify the fix
docker exec postgres-backup pg_dump --version
```

### Key Changes
1. **Removed** the generic `postgresql-client` package (installs v15)
2. **Added** `postgresql16-client` from Alpine edge repository
3. **Created symbolic links** for compatibility (`psql16` → `psql`, etc.)

---

## macOS zcat Compatibility Issue

### Error
```
zcat: can't stat: backups/postgres/dev/dev_backup_20250715_162501.sql.gz (backups/postgres/dev/dev_backup_20250715_162501.sql.gz.Z): No such file or directory
```

### Cause
On macOS, `zcat` expects `.Z` files (old Unix compress format), not `.gz` files. This causes the command to fail when trying to read gzipped backup files.

### Solution
Use `gunzip -c` instead of `zcat` for cross-platform compatibility:

```python
# In test files - replace zcat with gunzip -c
result = subprocess.run(
    ["gunzip", "-c", os.path.abspath(backup_file)],
    capture_output=True,
    text=True,
    timeout=60
)
```

### Alternative Solutions
1. **macOS-specific**: Use `gzcat` (works only on macOS)
```python
["gzcat", os.path.abspath(backup_file)]
```

2. **Python native**: Use gzip module (most portable)
```python
import gzip

with gzip.open(backup_file, 'rt') as f:
    content = f.read()
```

### Platform Differences
- **Linux**: `zcat` handles `.gz` files
- **macOS**: `zcat` expects `.Z` files, use `gzcat` or `gunzip -c` for `.gz`
- **Both**: `gunzip -c` works on all platforms

### Prevention
- Always use `gunzip -c` in scripts that need to be cross-platform
- Test on both macOS and Linux environments
- Consider using Python's gzip module for maximum portability

---

## Therapist Import Monitor Issues

### Error
```
ImportError: Failed to start therapist import monitor: THERAPIST_IMPORT_FOLDER_PATH environment variable is required
Monitor inactive for too long
High failure rate: 75.0%
```

### Cause
Issues with the local file monitoring system for therapist imports, including missing configuration, file system problems, or processing failures.

### Solution
1. **Check environment variables**:
```bash
echo $THERAPIST_IMPORT_FOLDER_PATH
echo $THERAPIST_IMPORT_CHECK_INTERVAL_SECONDS
```

2. **Verify file system permissions**:
```bash
# Check directory exists and is readable
ls -la $THERAPIST_IMPORT_FOLDER_PATH
# Check for recent files
find $THERAPIST_IMPORT_FOLDER_PATH -name "*.json" -mtime -1
```

3. **Check import status**:
```bash
curl http://localhost:8002/api/therapists/import-status
curl http://localhost:8002/health/import
```

4. **Review import logs**:
```bash
docker-compose logs therapist_service-dev | grep -i import
```

### Common Issues
- **Missing environment variables**: Set required `THERAPIST_IMPORT_FOLDER_PATH` and `THERAPIST_IMPORT_CHECK_INTERVAL_SECONDS`
- **File permission issues**: Ensure read permissions on import directory
- **Invalid JSON files**: Check file format matches expected schema
- **High failure rates**: Review error notifications for common validation issues

### Prevention
- Monitor import health endpoint regularly
- Set up alerts for import failures
- Validate JSON files before placing in import directory
- Ensure proper file system permissions

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