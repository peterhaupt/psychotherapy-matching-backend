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
ERROR: (psycopg2.errors.InvalidTextRepresentation) invalid input value for enum emailstatus: "SENT"
LINE 3: ...mestamp AND communication_service.emails.status = 'SENT' AND...
```

### Cause

This error occurs when using the enum *variant name* (e.g., `SENT`) in database queries instead of the enum's *string value* (e.g., `gesendet`). SQLAlchemy stores the string value in the database, not the enum name.

### Solution

Always use the enum's `.value` property when constructing database queries that filter by enum fields:

**Incorrect:**
```python
unanswered_emails = db.query(Email).filter(
    Email.sent_at <= seven_days_ago,
    Email.status == 'SENT',  # Wrong - uses the enum name
    Email.response_received.is_(False)
).all()
```

**Correct:**
```python
unanswered_emails = db.query(Email).filter(
    Email.sent_at <= seven_days_ago,
    cast(Email.status, String) == EmailStatus.SENT.value,  # Correct - uses enum value
    Email.response_received.is_(False)
).all()
```

### Best Practices for Database Enum Handling

1. **Always Use Enum Values**: 
   - When filtering by enum fields, always use `EnumClass.VARIANT.value`
   - Cast the database column to a string with `cast(Column, String)` when needed

2. **Consistent Query Patterns**:
   - Use the same pattern everywhere in your codebase
   - Create helper functions for common query patterns

3. **Database Migrations**:
   - Be careful with enum changes that might affect stored values
   - When changing enum values, create a migration to update existing records

4. **Parameterized Queries**:
   - Use query parameters rather than string concatenation