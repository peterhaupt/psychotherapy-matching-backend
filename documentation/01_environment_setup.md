# Environment Setup

## Summary
This document details the environment setup for the Psychotherapy Matching Platform. It covers the installation and configuration of core dependencies, Python environment, version control, project structure creation, and the three-environment deployment architecture.

## Core Dependencies

### System Configuration
```
Docker: Version 28.0.4, build b8034c0
Docker Compose: Version v2.34.0-desktop.1
Git: Version 2.48.1
Make: GNU Make 3.81
Python: Version 3.11.11 (via pyenv)
VS Code: Version 1.99.3 (Universal)
```

### Status
✅ Docker - Installed  
✅ Docker Compose - Installed  
✅ Git - Installed  
✅ Make - Installed  
✅ Python 3.11.11 - Installed via pyenv  
✅ Virtual Environment - Created with name "boona_MVP"  

## Python Environment Configuration

1. Python 3.11.11 installed via pyenv
2. Virtual environment created using pyenv virtualenv
3. `.python-version` file created to automatically activate environment
4. VS Code configured to use the pyenv virtual environment via settings.json

## Version Control Configuration

1. Git repository initialized
2. Standard Python .gitignore file created and extended with:
   - Docker-specific exclusions
   - Database files
   - Kafka data
   - Log files
   - Local configuration
   - IDE-specific files
   - Ensured database initialization scripts are NOT excluded from version control

## Three-Environment Architecture

The platform uses three completely isolated environments:

### 1. Development Environment
- **Purpose**: Active development and debugging
- **Docker Compose**: `docker-compose.dev.yml`
- **Configuration**: `.env.dev`
- **Port Range**: 8001-8005 (services), 5432/6432 (database)
- **Command**: `make dev` or `make start-dev`

### 2. Test Environment
- **Purpose**: Integration testing and pre-production validation
- **Docker Compose**: `docker-compose.test.yml`
- **Configuration**: `.env.test`
- **Port Range**: 8011-8015 (services), 5433/6433 (database)
- **Command**: `make start-test` or `make deploy-test`

### 3. Production Environment
- **Purpose**: Live production system
- **Docker Compose**: `docker-compose.prod.yml`
- **Configuration**: `.env.prod`
- **Port Range**: 8021-8025 (services), 5434/6434 (database)
- **Command**: `make start-prod` or `make deploy`

### Docker Compose References
Each environment has its own Docker Compose file with:
- Environment-specific service names (e.g., `patient_service-dev`, `patient_service-test`)
- Isolated networks (e.g., `curavani_backend_dev`, `curavani_backend_test`)
- Separate volumes for data persistence
- Health checks for proper service initialization

## Environment Variables

The platform uses over 80 environment variables for configuration. Key categories include:

### Database Configuration
- `DB_USER`, `DB_PASSWORD`, `DB_NAME`
- `DB_HOST`, `DB_PORT` (PostgreSQL)
- `PGBOUNCER_HOST`, `PGBOUNCER_PORT` (Connection pooling)

### Service Ports
Each service has environment-specific ports:
- `PATIENT_SERVICE_PORT` (8001/8011/8021)
- `THERAPIST_SERVICE_PORT` (8002/8012/8022)
- `MATCHING_SERVICE_PORT` (8003/8013/8023)
- `COMMUNICATION_SERVICE_PORT` (8004/8014/8024)
- `GEOCODING_SERVICE_PORT` (8005/8015/8025)

### External Services
- `KAFKA_BOOTSTRAP_SERVERS`, `KAFKA_ZOOKEEPER_CONNECT`
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`
- `OSM_API_URL`, `OSRM_API_URL` (Geocoding)

### Application Settings
- `FLASK_ENV` (development/testing/production)
- `SECRET_KEY` (Flask sessions)
- `LOG_LEVEL` (DEBUG/INFO/WARNING/ERROR)
- **CORS_ALLOWED_ORIGINS** (Frontend URLs for each environment)

### Example Configuration
See `.env.example` for complete list with descriptions.

## Project Structure

The project follows a microservice architecture with the following directory structure:

```
boona_MVP/
├── docker/                 # Docker configuration files
├── docker-compose.yml      # Container orchestration
├── docker-compose.dev.yml  # Development environment
├── docker-compose.test.yml # Test environment
├── docker-compose.prod.yml # Production environment
├── .env.example           # Configuration template
├── .env.dev              # Development configuration
├── .env.test             # Test configuration
├── .env.prod             # Production configuration
├── Makefile              # Deployment automation
├── shared/               # Shared code libraries
│   ├── models/           # Common data models
│   ├── utils/            # Utility functions
│   ├── kafka/            # Kafka helpers
│   ├── api/              # REST API utilities
│   ├── config/           # Centralized configuration
│   └── auth/             # Authentication modules
├── patient_service/      # Patient microservice
├── therapist_service/    # Therapist microservice
├── matching_service/     # Matching microservice
├── communication_service/# Communication microservice
├── geocoding_service/    # Geocoding microservice
├── scraping_service/     # Scraping microservice
├── migrations/           # Database migrations
├── scripts/              # Deployment scripts
├── backups/              # Database backups
└── tests/                # Test suites
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

## Development Approach

We're taking a step-by-step approach to implementation:

1. Basic Structure: Create minimal foundation first
2. Docker Configuration: Set up containerization environment with three environments
3. Iterative Service Implementation: Build and test one service at a time
4. Integration: Connect services incrementally
5. Test-First Deployment: Always deploy to test environment before production

## Getting Started

### Initial Setup
1. Clone the repository
2. Copy `.env.example` to `.env.dev`, `.env.test`, and `.env.prod`
3. Configure environment-specific settings in each `.env` file
4. Ensure Docker Desktop is running

### Development Workflow
```bash
# Start development environment
make dev

# Check service health
make health-check-dev

# View logs
make logs-dev

# Connect to development database
make db-dev

# Run migrations
make migrate-dev
```

### Deployment Workflow
```bash
# Deploy to test environment first
make deploy-test

# Run tests
make test-all-test

# If tests pass, deploy to production
make deploy

# Monitor production
make health-check
make logs-prod
```

For complete deployment procedures, see `documentation/12_deployment_and_operations.md`.