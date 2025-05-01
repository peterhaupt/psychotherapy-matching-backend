# Therapist Service

## Summary
This document details the implementation of the Therapist Service, the second microservice developed for the Psychotherapy Matching Platform. The service handles all therapist-related data and operations, including therapist profile management, availability tracking, and status management.

## Models Implementation

### Therapist Model (`therapist_service/models/therapist.py`)

The Therapist model is built using SQLAlchemy and implements all required fields according to the specifications:

```python
class Therapist(Base):
    """Therapist database model."""

    __tablename__ = "therapists"
    __table_args__ = {"schema": "therapist_service"}

    id = Column(Integer, primary_key=True, index=True)

    # Personal Information
    anrede = Column(String(10))
    titel = Column(String(20))
    vorname = Column(String(100), nullable=False)
    nachname = Column(String(100), nullable=False)
    strasse = Column(String(255))
    plz = Column(String(10))
    ort = Column(String(100))
    telefon = Column(String(50))
    fax = Column(String(50))
    email = Column(String(255))
    webseite = Column(String(255))

    # Professional Information
    kassensitz = Column(Boolean, default=True)
    geschlecht = Column(String(20))  # Derived from anrede or explicitly set
    telefonische_erreichbarkeit = Column(JSONB)  # Structure of availability times
    fremdsprachen = Column(JSONB)  # List of languages
    psychotherapieverfahren = Column(JSONB)  # List of therapy methods
    zusatzqualifikationen = Column(Text)
    besondere_leistungsangebote = Column(Text)

    # Contact History
    letzter_kontakt_email = Column(Date)
    letzter_kontakt_telefon = Column(Date)
    letztes_persoenliches_gespraech = Column(Date)

    # Availability
    freie_einzeltherapieplaetze_ab = Column(Date)
    freie_gruppentherapieplaetze_ab = Column(Date)

    # Status Information
    status = Column(
        SQLAlchemyEnum(TherapistStatus),
        default=TherapistStatus.ACTIVE
    )
    sperrgrund = Column(Text)
    sperrdatum = Column(Date)

    # Timestamps
    created_at = Column(Date, default=date.today)
    updated_at = Column(Date, onupdate=date.today)
```

### Status Enumeration

The service defines an enumeration for therapist status:

```python
class TherapistStatus(str, Enum):
    """Enumeration for therapist status values."""

    ACTIVE = "aktiv"
    BLOCKED = "gesperrt"
    INACTIVE = "inaktiv"
```

## API Implementation

### Flask Application (`therapist_service/app.py`)

The main Flask application is configured with RESTful API endpoints:

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
    api.add_resource(TherapistListResource, '/api/therapists')
    api.add_resource(TherapistResource, '/api/therapists/<int:therapist_id>')

    return app
```

### API Endpoints (`therapist_service/api/therapists.py`)

The service implements RESTful endpoints for therapist management:

#### TherapistResource
Handles individual therapist operations:
- `GET /api/therapists/<id>`: Retrieve a specific therapist
- `PUT /api/therapists/<id>`: Update an existing therapist
- `DELETE /api/therapists/<id>`: Delete a therapist

#### TherapistListResource
Handles collection operations:
- `GET /api/therapists`: Retrieve all therapists with optional filtering
- `POST /api/therapists`: Create a new therapist

### Request Parsing and Validation

API endpoints use Flask-RESTful's `reqparse` for request parsing and validation:

```python
parser = reqparse.RequestParser()
# Required fields
parser.add_argument('vorname', type=str, required=True,
                   help='Vorname is required')
parser.add_argument('nachname', type=str, required=True,
                   help='Nachname is required')
# Optional fields
parser.add_argument('anrede', type=str)
parser.add_argument('titel', type=str)
parser.add_argument('email', type=str)
# etc.
```

### Response Marshalling

Response data is consistently formatted using Flask-RESTful's marshalling:

```python
therapist_fields = {
    'id': fields.Integer,
    'anrede': fields.String,
    'titel': fields.String,
    'vorname': fields.String,
    'nachname': fields.String,
    'email': fields.String,
    'telefon': fields.String,
    'status': fields.String,
    # Additional fields...
}
```

## Event Management

### Event Producers (`therapist_service/events/producers.py`)

The service implements Kafka producers for different therapist events:

```python
def publish_therapist_created(
    therapist_id: int,
    therapist_data: Dict[str, Any]
) -> bool:
    """Publish an event when a new therapist is created."""
    return producer.send_event(
        topic=THERAPIST_TOPIC,
        event_type="therapist.created",
        payload={
            "therapist_id": therapist_id,
            "therapist_data": therapist_data
        },
        key=str(therapist_id)
    )
```

Four main event types are published:
1. `therapist.created`: When a new therapist is created
2. `therapist.updated`: When a therapist's data is updated
3. `therapist.blocked`: When a therapist is blocked for new requests
4. `therapist.unblocked`: When a previously blocked therapist is unblocked

### Event Consumers (`therapist_service/events/consumers.py`)

A framework for consuming patient events is provided, allowing the therapist service to react to changes in patient data:

```python
def handle_patient_event(event: EventSchema) -> None:
    """Handle events from the patient service."""
    # Implementation depends on specific use cases
```

## Docker Configuration

### Dockerfile (`therapist_service/Dockerfile`)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create a non-root user to run the application
RUN useradd -m appuser
USER appuser

# Set environment variables
ENV PYTHONPATH=/app
ENV FLASK_APP=app.py
ENV FLASK_ENV=development

EXPOSE 8002

CMD ["python", "app.py"]
```

### Docker Compose Configuration

```yaml
therapist-service:
  build: ./therapist_service
  depends_on:
    - pgbouncer
  ports:
    - "8002:8002"
  volumes:
    - ./therapist_service:/app
    - ./shared:/app/shared  # Mount shared directory
  environment:
    - DATABASE_URL=postgresql://boona:boona_password@pgbouncer:6432/therapy_platform
    - FLASK_APP=app.py
    - FLASK_ENV=development
    - PYTHONPATH=/app
  restart: unless-stopped
```

## Database Migration

A migration script creates the therapist table in the `therapist_service` schema:

```python
def upgrade() -> None:
    """Upgrade schema."""
    # Create TherapistStatus enum type
    therapist_status = sa.Enum('ACTIVE', 'BLOCKED', 'INACTIVE', name='therapiststatus')
    therapist_status.create(op.get_bind())
    
    # Create therapists table
    op.create_table('therapists',
        # Column definitions...
        sa.PrimaryKeyConstraint('id'),
        schema='therapist_service'
    )
    
    # Create index on id
    op.create_index(
        op.f('ix_therapist_service_therapists_id'), 
        'therapists', 
        ['id'], 
        unique=False, 
        schema='therapist_service'
    )
```

## Dependencies

The therapist service has the following dependencies specified in `therapist_service/requirements.txt`:

```
Flask==3.1.0
Flask-RESTful==0.3.10
SQLAlchemy==2.0.40
psycopg2-binary==2.9.10
flask-sqlalchemy==3.1.1
kafka-python==2.1.5
```

## Testing

### API Testing

The Therapist API can be tested using curl commands:

```bash
# Create a therapist
curl -X POST http://localhost:8002/api/therapists \
  -H "Content-Type: application/json" \
  -d '{"vorname":"Max","nachname":"Musterfrau","titel":"Dr."}'

# Retrieve all therapists
curl -X GET http://localhost:8002/api/therapists

# Update a therapist
curl -X PUT http://localhost:8002/api/therapists/1 \
  -H "Content-Type: application/json" \
  -d '{"status":"BLOCKED","sperrgrund":"Temporarily unavailable"}'

# Delete a therapist
curl -X DELETE http://localhost:8002/api/therapists/1
```

### Event Testing

Kafka events can be tested using the provided Docker-based testing approach:

```bash
python tests/integration/docker-kafka-test.py --topic therapist-events
```

## Development Best Practices

1. **Error Handling**:
   - All database operations are wrapped in try-except blocks
   - SQLAlchemy errors are properly handled and meaningful error messages returned
   - Consistent HTTP status codes (404 for not found, 500 for database errors)

2. **Code Structure**:
   - Separation of concerns: models, API endpoints, events
   - Consistent naming conventions
   - Proper docstrings and type hints
   - Flake8 compliance

3. **Event Management**:
   - Standardized event schema
   - Proper event type categorization
   - Comprehensive payload data
   - Error handling in event publication