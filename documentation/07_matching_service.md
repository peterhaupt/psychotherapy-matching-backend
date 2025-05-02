# Matching Service

## Summary
This document details the implementation of the Matching Service, the third microservice developed for the Psychotherapy Matching Platform. The service handles the matching algorithm between patients and therapists, including placement request management, matching criteria, and status tracking.

## Models Implementation

### Placement Request Model (`matching_service/models/placement_request.py`)

The Placement Request model is built using SQLAlchemy and implements all required fields according to the specifications:

```python
class PlacementRequest(Base):
    """Placement request database model."""

    __tablename__ = "placement_requests"
    __table_args__ = {"schema": "matching_service"}

    id = Column(Integer, primary_key=True, index=True)
    
    # References
    patient_id = Column(Integer, nullable=False)
    therapist_id = Column(Integer, nullable=False)
    
    # Status tracking
    status = Column(
        SQLAlchemyEnum(PlacementRequestStatus),
        default=PlacementRequestStatus.OPEN
    )
    
    # Contact tracking
    created_at = Column(Date, default=date.today)
    email_contact_date = Column(Date)
    phone_contact_date = Column(Date)
    
    # Response tracking
    response = Column(Text)
    response_date = Column(Date)
    next_contact_after = Column(Date)  # For rejected requests that can be retried
    
    # Additional metadata
    priority = Column(Integer, default=1)  # Higher numbers = higher priority
    notes = Column(Text)
```

### Status Enumeration

The service defines an enumeration for placement request statuses:

```python
class PlacementRequestStatus(str, Enum):
    """Enumeration for placement request status values."""

    OPEN = "offen"
    IN_PROGRESS = "in_bearbeitung"
    REJECTED = "abgelehnt"
    ACCEPTED = "angenommen"
```

## API Implementation

### Flask Application (`matching_service/app.py`)

The main Flask application is configured with RESTful API endpoints and Kafka consumers:

```python
def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Configure database connection
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "postgresql://boona:boona_password@pgbouncer:6432/therapy_platform"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialize RESTful API
    api = Api(app)

    # Register API endpoints
    api.add_resource(PlacementRequestListResource, '/api/placement-requests')
    api.add_resource(PlacementRequestResource, '/api/placement-requests/<int:request_id>')

    # Start Kafka consumers
    start_consumers()

    return app
```

### API Endpoints (`matching_service/api/matching.py`)

The service implements RESTful endpoints for placement request management:

#### PlacementRequestResource
Handles individual placement request operations:
- `GET /api/placement-requests/<id>`: Retrieve a specific placement request
- `PUT /api/placement-requests/<id>`: Update an existing placement request
- `DELETE /api/placement-requests/<id>`: Delete a placement request

#### PlacementRequestListResource
Handles collection operations:
- `GET /api/placement-requests`: Retrieve all placement requests with optional filtering
- `POST /api/placement-requests`: Create a new placement request

### Request Parsing and Validation

API endpoints use Flask-RESTful's `reqparse` for request parsing and validation:

```python
parser = reqparse.RequestParser()
parser.add_argument('patient_id', type=int, required=True,
                   help='Patient ID is required')
parser.add_argument('therapist_id', type=int, required=True,
                   help='Therapist ID is required')
parser.add_argument('status', type=str)
# etc.
```

## Matching Algorithm

The service includes a matching algorithm implementation in the `matching_service/algorithms/matcher.py` file, which provides the following key functions:

### Finding Matching Therapists

```python
def find_matching_therapists(
    patient_id: int,
    max_distance: Optional[float] = None,
    gender_preference: Optional[str] = None,
    excluded_therapist_ids: Optional[List[int]] = None
) -> List[Dict[str, Any]]:
    """Find matching therapists for a patient based on criteria."""
    # Algorithm logic
```

The algorithm considers multiple criteria:
- Patient location and therapist location (distance calculation)
- Patient gender preferences
- Excluded therapists list
- Therapist availability
- Previous placement requests (to avoid duplicates)

### Creating Placement Requests

```python
def create_placement_requests(
    patient_id: int,
    therapist_ids: List[int],
    notes: Optional[str] = None
) -> List[int]:
    """Create placement requests for a patient and multiple therapists."""
    # Implementation
```

This function handles creating multiple placement requests at once for efficient batch processing.

## Event Management

### Event Producers (`matching_service/events/producers.py`)

The service implements Kafka producers for different matching events:

```python
def publish_match_created(
    match_id: int,
    patient_id: int,
    therapist_id: int,
    match_data: Optional[Dict[str, Any]] = None
) -> bool:
    """Publish an event when a new match is created."""
    # Implementation
```

Two main event types are published:
1. `match.created`: When a new placement request is created
2. `match.status_changed`: When a placement request's status changes

### Event Consumers (`matching_service/events/consumers.py`)

The service consumes events from both the Patient and Therapist services:

```python
def handle_patient_event(event: EventSchema) -> None:
    """Handle events from the patient service."""
    # Implementation
```

```python
def handle_therapist_event(event: EventSchema) -> None:
    """Handle events from the therapist service."""
    # Implementation
```

Key event handling includes:
- Reacting to patient deletion (canceling all their placement requests)
- Reacting to therapist blocking (suspending placement requests)
- Updating placement requests when patients or therapists change

## Service Integration

### Communication with Other Services

The matching service integrates with the Patient and Therapist services through:

1. REST API Calls: For direct data retrieval
   ```python
   def get_patient_data(patient_id: int) -> Optional[Dict[str, Any]]:
       """Get patient data from the Patient Service."""
       # Implementation
   ```

2. Kafka Events: For asynchronous updates and notifications
   ```python
   def start_consumers():
       """Start all Kafka consumers for the Matching Service."""
       # Implementation
   ```

## Docker Configuration

### Docker Compose Configuration

```yaml
matching-service:
  build: ./matching_service
  depends_on:
    - pgbouncer
    - kafka
  ports:
    - "8003:8003"
  volumes:
    - ./matching_service:/app
    - ./shared:/app/shared
  environment:
    - DATABASE_URL=postgresql://boona:boona_password@pgbouncer:6432/therapy_platform
    - FLASK_APP=app.py
    - FLASK_ENV=development
    - PYTHONPATH=/app
  restart: unless-stopped
```

## Database Migration

A migration script creates the placement request table in the `matching_service` schema:

```python
def upgrade() -> None:
    """Upgrade schema."""
    # Create PlacementRequestStatus enum type
    placement_request_status = sa.Enum(
        'OPEN', 'IN_PROGRESS', 'REJECTED', 'ACCEPTED',
        name='placementrequeststatus'
    )
    placement_request_status.create(op.get_bind())
    
    # Create placement_requests table
    op.create_table('placement_requests',
        # Column definitions...
        sa.PrimaryKeyConstraint('id'),
        schema='matching_service'
    )
```

## Dependencies

The matching service has the following dependencies specified in `matching_service/requirements.txt`:

```
Flask==3.1.0
Flask-RESTful==0.3.10
SQLAlchemy==2.0.40
psycopg2-binary==2.9.10
flask-sqlalchemy==3.1.1
kafka-python==2.1.5
```

## Testing

### Algorithm Testing

A test script is provided for testing the matching algorithm:

```python
def main():
    """Run the matching algorithm test."""
    # Implementation
```

This script allows testing the matching algorithm with real data from the database.

## Future Enhancements

1. **Integration with Geocoding Service**: The current implementation includes placeholders for distance calculation that will be replaced with actual calculations once the Geocoding service is implemented.

2. **Advanced Matching Criteria**: The matching algorithm can be enhanced with additional criteria, such as:
   - Therapist specialization matching patient needs
   - Availability window matching
   - Public transportation considerations

3. **Machine Learning Integration**: Future versions could incorporate machine learning for optimizing matching success rates based on historical data.

## Development Best Practices

1. **Error Handling**:
   - All database operations are wrapped in try-except blocks
   - SQLAlchemy errors are properly handled and meaningful error messages returned
   - Consistent HTTP status codes (404 for not found, 500 for database errors)

2. **Code Structure**:
   - Separation of concerns: models, API endpoints, events, algorithms
   - Consistent naming conventions
   - Proper docstrings and type hints
   - Flake8 compliance

3. **Event Management**:
   - Standardized event schema
   - Proper event type categorization
   - Comprehensive payload data
   - Error handling in event publication and consumption