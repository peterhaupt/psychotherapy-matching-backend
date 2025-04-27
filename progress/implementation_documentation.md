# Psychotherapy Matching Platform Implementation Documentation

## Environment Setup

### Current System Configuration

```
Docker: Version 28.0.4, build b8034c0
Docker Compose: Version v2.34.0-desktop.1
Git: Version 2.48.1
Make: GNU Make 3.81
Python: Version 3.11.11 (via pyenv)
VS Code: Version 1.99.3 (Universal)
```

### Core Dependencies Status

✅ Docker - Installed  
✅ Docker Compose - Installed  
✅ Git - Installed  
✅ Make - Installed  
✅ Python 3.11.11 - Installed via pyenv  
✅ Virtual Environment - Created with name "boona_MVP"  

### Python Environment Configuration

1. Python 3.11.11 installed via pyenv
2. Virtual environment created:
   ```bash
   pyenv virtualenv 3.11.11 boona_MVP
   ```
3. `.python-version` file created to automatically activate environment:
   ```bash
   echo boona_MVP > .python-version
   ```
4. VS Code configured to use the pyenv virtual environment

### Version Control Configuration

1. Git repository already initialized
2. Standard Python .gitignore file created and extended with:
   - Docker-specific exclusions
   - Database files
   - Kafka data
   - Log files
   - Local configuration
   - IDE-specific files

## Implementation Approach

We're taking a step-by-step approach to implementation:

1. **Basic Structure**: Create minimal foundation first
2. **Docker Configuration**: Set up containerization environment
3. **Iterative Service Implementation**: Build and test one service at a time
4. **Integration**: Connect services incrementally

### Directory Structure Plan

```
boona_MVP/
├── docker/                 # Docker configuration files
├── docker-compose.yml      # Container orchestration
├── shared/                 # Shared code libraries
│   ├── models/             # Common data models
│   ├── utils/              # Utility functions
│   ├── kafka/              # Kafka helpers
│   ├── api/                # REST API utilities
│   └── auth/               # Authentication modules
├── patient_service/        # Patient microservice
├── therapist_service/      # Therapist microservice
├── matching_service/       # Matching microservice
├── communication_service/  # Communication microservice
├── geocoding_service/      # Geocoding microservice
└── scraping_service/       # Scraping microservice
```

Each service follows a similar structure:
```
service-name/
├── api/                  # API endpoints
├── models/               # Service-specific models
├── events/               # Kafka producers/consumers
├── templates/            # HTML templates
├── static/               # CSS, JS, etc.
├── tests/                # Unit and integration tests
├── Dockerfile            # Container definition
└── requirements.txt      # Python dependencies
```

## Implementation Progress

### Project Structure Setup ✅

1. Created base project directory structure:
   ```
   boona_MVP/
   ├── docker/                 # Docker configuration files
   ├── docker-compose.yml      # Container orchestration
   ├── shared/                 # Shared code libraries
   │   ├── models/             # Common data models
   │   ├── utils/              # Utility functions
   │   ├── kafka/              # Kafka helpers
   │   ├── api/                # REST API utilities
   │   └── auth/               # Authentication modules
   ├── patient_service/        # Patient microservice
   │   ├── api/                # API endpoints
   │   ├── models/             # Service-specific models
   │   ├── events/             # Kafka producers/consumers
   │   ├── templates/          # HTML templates
   │   ├── static/             # CSS, JS, etc.
   │   └── tests/              # Unit and integration tests
   ├── therapist_service/      # Therapist microservice
   ├── matching_service/       # Matching microservice
   ├── communication_service/  # Communication microservice
   ├── geocoding_service/      # Geocoding microservice
   └── scraping_service/       # Scraping microservice
   ```

### Database Setup ✅

1. Created docker-compose.yml with PostgreSQL configuration:
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

2. Created database schema initialization scripts:
   ```sql
   -- Create schemas for each service
   CREATE SCHEMA IF NOT EXISTS patient_service;
   CREATE SCHEMA IF NOT EXISTS therapist_service;
   CREATE SCHEMA IF NOT EXISTS matching_service;
   CREATE SCHEMA IF NOT EXISTS communication_service;
   CREATE SCHEMA IF NOT EXISTS geocoding_service;
   CREATE SCHEMA IF NOT EXISTS scraping_service;
   ```

3. Set up PgBouncer for connection pooling:
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

4. Configured Alembic for database migrations:
   - Created migrations directory
   - Initialized Alembic
   - Added service-specific migration directories

### Python Dependencies Setup ✅

1. Created requirements.txt with production dependencies:
   - Flask for web framework
   - SQLAlchemy for ORM
   - psycopg2-binary for PostgreSQL connectivity
   - Alembic for database migrations
   - kafka-python for Kafka integration
   - Flask-SQLAlchemy for Flask-SQLAlchemy integration
   - Flask-RESTful for API development

2. Created requirements-dev.txt with development dependencies:
   - pytest and pytest-cov for testing
   - black, flake8, and isort for code formatting and linting
   - mypy for type checking

3. Created shared database configuration:
   ```python
   # shared/utils/database.py
   from sqlalchemy import create_engine
   from sqlalchemy.ext.declarative import declarative_base
   from sqlalchemy.orm import sessionmaker

   DATABASE_URL = "postgresql://boona:boona_password@pgbouncer:6432/therapy_platform"

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

### Patient Service Implementation ✅

1. Created Patient Database Models:
   - Implemented SQLAlchemy model for Patient entity in `patient-service/models/patient.py`
   - Created enums for PatientStatus and TherapistGenderPreference
   - Added all required fields from the specifications
   - Implemented proper relationships and constraints
   - Ensured Flake8 compliance with proper docstrings and code formatting

2. Created Patient Service API:
   - Implemented Flask application structure in `patient-service/app.py`
   - Created RESTful API endpoints in `patient-service/api/patients.py`
   - Implemented CRUD operations (Create, Read, Update, Delete)
   - Added support for filtering patients by status
   - Implemented error handling and proper HTTP status codes
   - Set up marshalling for consistent API responses

3. Set Up Docker Environment:
   - Created Dockerfile for patient service with Python 3.11
   - Set up proper environment variables and configuration
   - Added non-root user for security
   - Updated docker-compose.yml to include patient service
   - Configured volume mapping for development

4. Fixed Import Issues:
   - Corrected import paths to work correctly with the hyphenated directory structure
   - Updated imports in app.py from `patient_service.api.patients` to relative imports `api.patients`
   - Fixed imports in patients.py from `patient_service.models.patient` to relative imports `models.patient`
   - Ensured code follows Flake8 standards including proper line breaks and whitespace management

## Current Status

- [x] Verify core dependencies
- [x] Set up Python environment
- [x] Create project structure
- [x] Set up database
- [x] Install essential Python dependencies
- [x] Implement patient service models
- [x] Create patient service API
- [x] Set up Docker environment for patient service
- [ ] Create database migrations
- [ ] Configure message queue
- [ ] Implement therapist service
- [ ] Develop matching service
- [ ] Create communication service
- [ ] Implement web interface
- [ ] Set up geocoding service
- [ ] Implement web scraping

## Known Issues and Fixes

### Import Issues in Patient Service

The patient_service had issues with import paths due to the hyphenated directory name. Python module names can't contain hyphens, causing the imports to fail. We've renamed the directories to use underscores to fix this issue.

**Original Problematic Code:**
```python
# In app.py
from patient_service.api.patients import (
    PatientResource, PatientListResource
)

# In api/patients.py
from patient_service.models.patient import Patient, PatientStatus
```

**Fixed Code:**
```python
# In app.py
from api.patients import PatientResource, PatientListResource

# In api/patients.py
from models.patient import Patient, PatientStatus
```

This fix ensures that the imports work correctly with the project's directory structure. Additionally, we've renamed all hyphenated directories to use underscores (e.g., `patient-service` → `patient_service`) while keeping the service names with hyphens in docker-compose.yml and documentation.

## Next Steps

### 1. Create Database Migrations

1. Update Alembic configuration to include the patient models:
   ```bash
   mkdir -p migrations/alembic/versions
   ```

2. Configure Alembic to detect the SQLAlchemy models:
   - Update env.py to import the models
   - Set target_metadata to the Base.metadata

3. Create initial migration for patient service:
   ```bash
   cd migrations
   alembic revision --autogenerate -m "create patient table"
   ```

4. Apply migrations:
   ```bash
   alembic upgrade head
   ```

### 2. Configure Message Queue

1. Update docker-compose.yml to add Kafka and Zookeeper:
   ```yaml
   zookeeper:
     image: confluentinc/cp-zookeeper:latest
     environment:
       ZOOKEEPER_CLIENT_PORT: 2181
     ports:
       - "2181:2181"

   kafka:
     image: confluentinc/cp-kafka:latest
     depends_on:
       - zookeeper
     ports:
       - "9092:9092"
     environment:
       KAFKA_BROKER_ID: 1
       KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
       KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
       KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
   ```

2. Create Kafka topic configuration script:
   ```bash
   mkdir -p docker/kafka
   touch docker/kafka/create-topics.sh
   ```

3. Implement Kafka events for patient service:
   - Create patient_service/events directory
   - Implement producers and consumers for patient events
   - Set up event schemas for patient creation, updates, etc.

### 3. Implement Therapist Service

1. Create therapist database models:
   ```bash
   mkdir -p therapist_service/models
   touch therapist_service/models/__init__.py
   touch therapist_service/models/therapist.py
   ```

2. Define SQLAlchemy models based on requirements:
   - Create SQLAlchemy classes for Therapist entity
   - Implement all fields from the requirements
   - Add relationships to other entities

3. Create Therapist Service API structure:
   ```bash
   touch therapist_service/app.py
   mkdir -p therapist_service/api
   touch therapist_service/api/__init__.py
   touch therapist_service/api/therapists.py
   ```

4. Implement basic API endpoints:
   - Create therapist
   - Get therapist by ID
   - Update therapist
   - List therapists with filtering
   - Blocking/unblocking functionality

5. Create Docker configuration:
   ```bash
   touch therapist_service/Dockerfile
   touch therapist_service/requirements.txt
   ```

6. Update docker-compose.yml to include therapist service

### 4. Develop Matching Service

Follow similar steps to implement the matching service, focusing on the core matching algorithm and workflows.