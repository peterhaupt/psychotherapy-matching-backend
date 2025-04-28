# Patient Service

## Summary
This document details the implementation of the Patient Service, the first microservice developed for the Psychotherapy Matching Platform. The service handles all patient-related data and operations, including patient profile management, medical information handling, preference tracking, and patient state management.

## Models Implementation

### Patient Model (`patient_service/models/patient.py`)

The Patient model is built using SQLAlchemy and implements all required fields according to the specifications:

```python
class Patient(Base):
    """Patient database model."""

    __tablename__ = "patients"
    __table_args__ = {"schema": "patient_service"}

    id = Column(Integer, primary_key=True, index=True)

    # Personal Information
    anrede = Column(String(10))
    vorname = Column(String(100), nullable=False)
    nachname = Column(String(100), nullable=False)
    strasse = Column(String(255))
    plz = Column(String(10))
    ort = Column(String(100))
    email = Column(String(255))
    telefon = Column(String(50))

    # Medical Information
    hausarzt = Column(String(255))
    krankenkasse = Column(String(100))
    krankenversicherungsnummer = Column(String(50))
    geburtsdatum = Column(Date)
    diagnose = Column(String(50))  # ICD-10 Diagnose

    # Process Status
    vertraege_unterschrieben = Column(Boolean, default=False)
    psychotherapeutische_sprechstunde = Column(Boolean, default=False)
    startdatum = Column(Date)  # Beginn der Platzsuche
    erster_therapieplatz_am = Column(Date)
    funktionierender_therapieplatz_am = Column(Date)
    status = Column(
        SQLAlchemyEnum(PatientStatus),
        default=PatientStatus.OPEN
    )
    empfehler_der_unterstuetzung = Column(Text)

    # Availability
    zeitliche_verfuegbarkeit = Column(JSONB)  # Wochentage und Uhrzeiten
    raeumliche_verfuegbarkeit = Column(JSONB)  # Maximale Entfernung/Fahrzeit
    verkehrsmittel = Column(String(50))  # Auto oder ÖPNV

    # Preferences
    offen_fuer_gruppentherapie = Column(Boolean, default=False)
    offen_fuer_diga = Column(Boolean, default=False)  # Digitale Anwendungen
    letzter_kontakt = Column(Date)

    # Medical History
    psychotherapieerfahrung = Column(Boolean, default=False)
    stationaere_behandlung = Column(Boolean, default=False)
    berufliche_situation = Column(Text)
    familienstand = Column(String(50))
    aktuelle_psychische_beschwerden = Column(Text)
    beschwerden_seit = Column(Date)
    bisherige_behandlungen = Column(Text)
    relevante_koerperliche_erkrankungen = Column(Text)
    aktuelle_medikation = Column(Text)
    aktuelle_belastungsfaktoren = Column(Text)
    unterstuetzungssysteme = Column(Text)

    # Therapy Goals and Expectations
    anlass_fuer_die_therapiesuche = Column(Text)
    erwartungen_an_die_therapie = Column(Text)
    therapieziele = Column(Text)
    fruehere_therapieerfahrungen = Column(Text)

    # Therapist Exclusions and Preferences
    ausgeschlossene_therapeuten = Column(JSONB)  # Liste von Therapeuten-IDs
    bevorzugtes_therapeutengeschlecht = Column(
        SQLAlchemyEnum(TherapistGenderPreference),
        default=TherapistGenderPreference.ANY
    )

    # Timestamps
    created_at = Column(Date, default=date.today)
    updated_at = Column(Date, onupdate=date.today)
```

### Status Enumerations

The service defines enumerations for patient statuses and therapist gender preferences:

```python
class PatientStatus(str, Enum):
    """Enumeration for patient status values."""

    OPEN = "offen"
    SEARCHING = "auf der Suche"
    IN_THERAPY = "in Therapie"
    THERAPY_COMPLETED = "Therapie abgeschlossen"
    SEARCH_ABORTED = "Suche abgebrochen"
    THERAPY_ABORTED = "Therapie abgebrochen"


class TherapistGenderPreference(str, Enum):
    """Enumeration for therapist gender preferences."""

    MALE = "Männlich"
    FEMALE = "Weiblich"
    ANY = "Egal"
```

## API Implementation

### Flask Application (`patient_service/app.py`)

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
    api.add_resource(PatientListResource, '/api/patients')
    api.add_resource(PatientResource, '/api/patients/<int:patient_id>')

    return app
```

### API Endpoints (`patient_service/api/patients.py`)

The service implements RESTful endpoints for patient management:

#### PatientResource
Handles individual patient operations:
- `GET /api/patients/<id>`: Retrieve a specific patient
- `PUT /api/patients/<id>`: Update an existing patient
- `DELETE /api/patients/<id>`: Delete a patient

#### PatientListResource
Handles collection operations:
- `GET /api/patients`: Retrieve all patients with optional filtering
- `POST /api/patients`: Create a new patient

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
parser.add_argument('email', type=str)
parser.add_argument('telefon', type=str)
```

### Response Marshalling

Response data is consistently formatted using Flask-RESTful's marshalling:

```python
patient_fields = {
    'id': fields.Integer,
    'anrede': fields.String,
    'vorname': fields.String,
    'nachname': fields.String,
    'email': fields.String,
    'telefon': fields.String,
    'status': fields.String,
    # Additional fields...
}
```

## Docker Configuration

### Dockerfile (`patient_service/Dockerfile`)

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

EXPOSE 8001

CMD ["python", "app.py"]
```

### Docker Compose Configuration

```yaml
patient-service:
  build: ./patient_service
  depends_on:
    - pgbouncer
  ports:
    - "8001:8001"
  volumes:
    - ./patient_service:/app
    - ./shared:/app/shared  # Mount shared directory
  environment:
    - DATABASE_URL=postgresql://boona:boona_password@pgbouncer:6432/therapy_platform
    - FLASK_APP=app.py
    - FLASK_ENV=development
    - PYTHONPATH=/app
  restart: unless-stopped
```

## Dependencies

The patient service has the following dependencies specified in `patient_service/requirements.txt`:

```
Flask==3.1.0
Flask-RESTful==0.3.10
SQLAlchemy==2.0.40
psycopg2-binary==2.9.10
flask-sqlalchemy==3.1.1
```

## Development Best Practices

1. **Error Handling**:
   - All database operations are wrapped in try-except blocks
   - SQLAlchemy errors are properly handled and meaningful error messages returned
   - Consistent HTTP status codes (404 for not found, 500 for database errors)

2. **Code Structure**:
   - Separation of concerns: models, API endpoints
   - Consistent naming conventions
   - Proper docstrings and type hints
   - Flake8 compliance

3. **Database Operations**:
   - Proper session management (open, commit, close)
   - Rollbacks in case of errors
   - Transaction consistency