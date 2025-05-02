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