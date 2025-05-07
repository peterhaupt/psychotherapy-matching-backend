# Common Errors in the Therapy Matching Platform

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

When you try to create or update a record with `"status": "IN_PROGRESS"` in the JSON payload, Python tries to convert this string to the enum using `PlacementRequestStatus(value)`. This fails because `"IN_PROGRESS"` isn't one of the valid string values defined in the enum.

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
   - Example: Accept both `"IN_PROGRESS"` and `"in_bearbeitung"` in the API

4. **Error Messages**:
   - Improve error messages to list valid options
   - Example: `ValueError: 'IN_PROGRESS' is not a valid PlacementRequestStatus. Valid values are: "offen", "in_bearbeitung", "abgelehnt", "angenommen"`

5. **Testing**:
   - Create comprehensive API tests for each enum value
   - Test both valid and invalid values to ensure proper error handling

### Implementation Examples

To improve the API implementation, consider the following code modifications:

#### Option 1: Better Error Handling

```python
try:
    placement_request.status = PlacementRequestStatus(value)
except ValueError:
    # Provide a more helpful error message
    valid_values = [status.value for status in PlacementRequestStatus]
    return {
        'message': f"Invalid status value '{value}'. Valid values are: {valid_values}"
    }, 400
```

#### Option 2: Value Translation Layer

```python
# Map external-facing values to internal enum values
STATUS_MAPPING = {
    "OPEN": "offen",
    "IN_PROGRESS": "in_bearbeitung",
    "REJECTED": "abgelehnt",
    "ACCEPTED": "angenommen",
    # Also include the original values for flexibility
    "offen": "offen",
    "in_bearbeitung": "in_bearbeitung",
    "abgelehnt": "abgelehnt",
    "angenommen": "angenommen"
}

# In the API code:
if key == 'status' and value:
    mapped_value = STATUS_MAPPING.get(value)
    if mapped_value:
        placement_request.status = PlacementRequestStatus(mapped_value)
    else:
        valid_values = list(STATUS_MAPPING.keys())
        return {
            'message': f"Invalid status value '{value}'. Valid values are: {valid_values}"
        }, 400
```

#### Option 3: Redesign Enums for API Consistency

```python
class PlacementRequestStatus(str, Enum):
    """Enumeration for placement request status values."""
    
    # Use uppercase strings for both names and values
    OPEN = "OPEN"  
    IN_PROGRESS = "IN_PROGRESS"
    REJECTED = "REJECTED"
    ACCEPTED = "ACCEPTED"
    
    # Add a property for display/human-readable values
    @property
    def display_name(self):
        display_values = {
            "OPEN": "Offen",
            "IN_PROGRESS": "In Bearbeitung",
            "REJECTED": "Abgelehnt",
            "ACCEPTED": "Angenommen"
        }
        return display_values.get(self.value, self.value)
```

Remember that modifying the enum structure may require database migrations if the values are stored in the database.

## Database Enum Value Mismatch

### Error Description

When querying database records using Enum fields, you might encounter errors like this:

```
ERROR: (psycopg2.errors.InvalidTextRepresentation) invalid input value for enum emailstatus: "SENT"
LINE 3: ...mestamp AND communication_service.emails.status = 'SENT' AND...
```

### Cause

This error occurs when using the enum *variant name* (e.g., `SENT`) in database queries instead of the enum's *string value* (e.g., `gesendet`). SQLAlchemy stores the string value in the database, not the enum name.

In the Python code, the `EmailStatus` enum is defined with German values:

```python
class EmailStatus(str, Enum):
    """Enumeration for email status values."""

    DRAFT = "entwurf"
    QUEUED = "in_warteschlange"
    SENDING = "wird_gesendet"
    SENT = "gesendet"        # Note the German string value
    FAILED = "fehlgeschlagen"
```

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
   - For example: `filter(cast(Email.status, String) == EmailStatus.SENT.value)`

### Implementation Examples

#### Example 1: Proper Enum Filtering

```python
# Import the cast function for type casting
from sqlalchemy import cast, String

# Then in your query:
seven_days_ago = datetime.utcnow() - timedelta(days=7)
unanswered_emails = db.query(Email).filter(
    Email.sent_at <= seven_days_ago,
    cast(Email.status, String) == EmailStatus.SENT.value,
    Email.response_received.is_(False)
).all()
```

#### Example 2: Helper Function for Consistent Queries

```python
def filter_by_enum_status(query, model_class, status_field, enum_value):
    """Filter a query by an enum status value.
    
    Args:
        query: SQLAlchemy query object
        model_class: Model class being queried
        status_field: Name of the status field
        enum_value: Enum value to filter by
        
    Returns:
        Updated query with the filter applied
    """
    from sqlalchemy import cast, String
    
    field = getattr(model_class, status_field)
    return query.filter(cast(field, String) == enum_value.value)

# Using the helper:
query = db.query(Email)
query = filter_by_enum_status(query, Email, 'status', EmailStatus.SENT)
unanswered_emails = query.filter(
    Email.sent_at <= seven_days_ago,
    Email.response_received.is_(False)
).all()
```

#### Example 3: Creating a Custom Comparator Class

For more advanced usage, you could create a custom comparator class:

```python
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import type_coerce, String

class EnumComparator(Comparator):
    def __eq__(self, other):
        if isinstance(other, Enum):
            other = other.value
        return cast(self.expr, String).__eq__(other)

class MyModel(Base):
    # ...
    status = Column(SQLAlchemyEnum(MyEnum))
    
    @hybrid_property
    def status_str(self):
        return self.status.value if self.status else None
        
    @status_str.comparator
    def status_str(cls):
        return EnumComparator(cls.status)

# Then use it like:
query = db.query(MyModel).filter(MyModel.status_str == MyEnum.VALUE)
```

This approach is more complex but can make querying enums more intuitive across your codebase.