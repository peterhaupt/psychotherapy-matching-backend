# Common Errors in the Therapy Matching Platform

## Kafka Connection Issues

### Error Description

When starting services, you might see the following error in the logs:

```
Failed to connect to Kafka: NoBrokersAvailable
```

### Cause

This error occurs when services start before Kafka is fully initialized and ready to accept connections. In a containerized environment, Docker might start containers in the correct order, but the Kafka service inside its container needs additional time to initialize.

### Solution

This issue has been addressed with two complementary approaches:

1. **Application-level resilience**: The `RobustKafkaProducer` handles connection failures gracefully, queuing messages until Kafka becomes available. The error in the logs is expected and doesn't indicate a problem as long as services continue running.

2. **Container orchestration**: Docker Compose health checks ensure services wait for dependencies to be fully ready.

### Best Practices

1. **Always use the RobustKafkaProducer**:
   - Non-blocking initialization allows services to start regardless of Kafka status
   - Message queuing ensures no events are lost
   - Automatic reconnection handles transient failures

2. **Configure service dependencies properly**:
   - Use `condition: service_healthy` instead of simple `depends_on`
   - Add appropriate health checks to critical services
   - Allow sufficient time for service initialization with `start_period`

3. **Understand startup logs**:
   - Initial "Failed to connect" messages are normal and handled by the RobustKafkaProducer
   - Check subsequent logs for successful connections
   - Verify message delivery once Kafka is available

## PgBouncer Health Check Issues

### Error Description

When using health checks with PgBouncer, you might see:

```
dependency failed to start: container boona_mvp-pgbouncer-1 is unhealthy
```

### Cause

Standard network-based health checks using `nc` (netcat) fail because the tool is not available in the PgBouncer container, or the port check approach is not appropriate for this container.

### Solution

Use a socket-based health check that verifies the Unix socket file exists.

## Enum Value Mismatch in API Requests

### Error Description

When updating a placement request status through the API, you might encounter this error:

```
ValueError: 'IN_PROGRESS' is not a valid PlacementRequestStatus
```

### Cause

This error occurs when sending the enum *variant name* (e.g., `IN_PROGRESS`) in the API request instead of the enum's *string value* (e.g., `in_bearbeitung`).

In the Python code, the `PlacementRequestStatus` enum is defined as:

```python
class PlacementRequestStatus(str, Enum):
    """Enumeration for placement request status values."""

    OPEN = "offen"
    IN_PROGRESS = "in_bearbeitung"  # Note the German string value
    REJECTED = "abgelehnt"
    ACCEPTED = "angenommen"
```

### Solution

Use the string value instead of the enum name in your API requests:

**Incorrect:**
```bash
curl -X PUT http://localhost:8003/api/placement-requests/1 \
  -H "Content-Type: application/json" \
  -d '{"status":"IN_PROGRESS"}'
```

**Correct:**
```bash
curl -X PUT http://localhost:8003/api/placement-requests/1 \
  -H "Content-Type: application/json" \
  -d '{"status":"in_bearbeitung"}'
```

### Best Practices to Avoid This Error

1. **API Documentation**: 
   - Document all enum values explicitly in the API documentation
   - Include both the internal names and the expected string values

2. **Consistent Naming**:
   - Consider using the same string for both the enum name and value
   - Example: `OPEN = "OPEN"` instead of `OPEN = "offen"`
   - Alternatively, use lowercase for both: `open = "open"`

3. **API Validation**:
   - Add a translation layer in the API that maps external-facing values to internal enum values

4. **Error Messages**:
   - Improve error messages to list valid options

5. **Testing**:
   - Create comprehensive API tests for each enum value
   - Test both valid and invalid values to ensure proper error handling

## Database Enum Value Mismatch

### Error Description

When querying database records using Enum fields, you might encounter errors like this:

```
ERROR: (psycopg2.errors.InvalidTextRepresentation) invalid input value for enum emailstatus: "DRAFT"
LINE 3: ...mestamp AND communication_service.emails.status = 'DRAFT' AND...
```

### Cause

This error occurs when there's a mismatch between enum handling in SQLAlchemy and PostgreSQL:

1. **Python Code**: Enum classes define values (e.g., `DRAFT = "entwurf"`)
2. **Database**: PostgreSQL expects specific enum values (either `DRAFT` or `entwurf`)
3. **SQLAlchemy**: May convert between Python enum objects and database values incorrectly

#### Issues That Can Cause The Mismatch

1. **Inconsistent migration scripts**: If some migrations define enum types with English names and others with German values
2. **Direct usage of enum objects**: Using `EmailStatus.DRAFT` directly instead of `EmailStatus.DRAFT.value`
3. **String casting**: Different behavior when casting to strings vs. accessing the value property

### Solution

Always use the enum's `.value` property when constructing database queries that filter by enum fields:

**Incorrect:**
```python
unanswered_emails = db.query(Email).filter(
    Email.sent_at <= seven_days_ago,
    Email.status == EmailStatus.SENT,  # Wrong - uses the enum object
    Email.response_received.is_(False)
).all()
```

**Correct:**
```python
unanswered_emails = db.query(Email).filter(
    Email.sent_at <= seven_days_ago,
    Email.status == EmailStatus.SENT.value,  # Correct for string comparisons
    # OR cast the database column
    cast(Email.status, String) == EmailStatus.SENT.value,  # When comparing as strings
    Email.response_received.is_(False)
).all()
```

For object assignment, use the enum object directly (SQLAlchemy will handle conversion):

```python
email.status = EmailStatus.DRAFT  # Correct for property assignment
```

### Database Schema Consistency Check

To verify how enum values are stored in the database:

```sql
SELECT n.nspname as enum_schema,  
       t.typname as enum_name,  
       e.enumlabel as enum_value
FROM pg_type t 
JOIN pg_enum e ON t.oid = e.enumtypid  
JOIN pg_catalog.pg_namespace n ON n.oid = t.typnamespace
ORDER BY enum_schema, enum_name, e.enumsortorder;
```

### Fixing Inconsistent Enum Storage

If you find inconsistencies in how enum values are stored, create a migration to standardize them:

```python
def upgrade() -> None:
    """Update enum values to be consistent."""
    # Example: Update from German to English values
    op.execute("ALTER TYPE emailstatus RENAME TO emailstatus_old")
    op.execute("CREATE TYPE emailstatus AS ENUM ('DRAFT', 'QUEUED', 'SENDING', 'SENT', 'FAILED')")
    
    # Create a mapping between old and new values
    mapping = """
    CASE status::text
        WHEN 'entwurf' THEN 'DRAFT'::emailstatus
        WHEN 'in_warteschlange' THEN 'QUEUED'::emailstatus
        ...
    END
    """
    
    op.execute(f"ALTER TABLE communication_service.emails ALTER COLUMN status TYPE emailstatus USING {mapping}")
    op.execute("DROP TYPE emailstatus_old")
```

### Best Practices for Database Enum Handling

1. **Consistent Migration Strategy**: 
   - Use the same approach for all enum types
   - Store either all enum names or all enum values in the database
   - Document your convention

2. **Explicit Type Casting**:
   - When filtering by enum columns, always use explicit casting for consistent behavior
   - Use `cast(Column, String)` when comparing string values

3. **Migration Testing**:
   - Test migrations thoroughly in development before applying to production
   - Verify enum values in the database after migrations

4. **Schema Consistency Checks**:
   - Periodically verify enum definitions in the database match expected values
   - Add schema validation tests to your CI pipeline

5. **Defensive Coding**:
   - Add debug logging for enum values in critical operations
   - Handle potential enum conversion errors gracefully

## PostgreSQL Connection Issues

### Error Description

You may see errors like this in PostgreSQL logs:

```
FATAL: database "boona" does not exist
```

### Cause

This typically happens when a connection attempt doesn't specify a database name. PostgreSQL defaults to using a database with the same name as the user.

### Solution

1. **Check healthcheck configurations**:
   - Ensure database healthchecks specify a database name with `-d`
   - Example: `pg_isready -U boona -d therapy_platform`

2. **Verify connection strings**:
   - All database connection strings should explicitly include the database name
   - Both direct PostgreSQL and PgBouncer connections

3. **Create default database**:
   - If necessary, create a database with the same name as the user
   - `CREATE DATABASE boona OWNER boona;`

### Best Practices

1. **Always specify database name** in connection strings and health checks
2. **Use consistent connection parameters** across all services
3. **Check PostgreSQL logs** for connection errors
4. **Consider using dedicated health check users** with appropriate permissions

## Flask-RESTful RequestParser Default Value Handling

### Error Description

When using Flask-RESTful's `reqparse.RequestParser` with default values for optional fields, the defaults may not be applied as expected, resulting in errors like:

```
sqlalchemy.exc.IntegrityError: (psycopg2.errors.NotNullViolation) 
null value in column "sender_email" of relation "emails" violates not-null constraint
```

### Cause

The Flask-RESTful `RequestParser` adds all defined arguments to the result dictionary, even when they're not provided in the request. For parameters not included in the request, it adds them with a value of `None` rather than omitting them entirely.

When using the `.get(key, default)` method on the result dictionary, the default value is only used if the key doesn't exist at all - not if it exists with a value of `None`.

```python
# This won't use the default if 'sender_email' exists with a value of None
sender_email = args.get('sender_email', smtp_settings['sender'])
```

### Solution

Use the Python `or` operator instead of relying solely on `get()`'s default parameter:

```python
# This will use smtp_settings['sender'] if args.get('sender_email') is None
sender_email = args.get('sender_email') or smtp_settings['sender']
```

Another approach is to explicitly check for None:

```python
sender_email = args.get('sender_email')
if sender_email is None:
    sender_email = smtp_settings['sender']
```

### Best Practices for Default Value Handling

1. **Understand RequestParser behavior**:
   - Be aware that defined but unspecified arguments get `None` values
   - Don't rely on `get()`'s default parameter alone

2. **Use explicit None checks**:
   - Use the `or` operator for simple defaults
   - Use explicit if-checks for more complex logic

3. **Consider adding validation**:
   - Add validation to ensure required values are properly set before database operations
   - Log warning messages when defaults are applied

4. **Add debug logging**:
   - Log values at critical points to catch issues early
   - Check object attributes before database operations

5. **Test edge cases**:
   - Test API endpoints with missing optional fields
   - Verify default values are correctly applied