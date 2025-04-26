# Psychotherapy Matching Platform - Technical Architecture

## Overview

This document outlines the complete technical architecture for implementing the Psychotherapy Matching Platform, a microservice-based system for matching patients with therapists in Germany.

## 1. Technology Stack

### Core Technologies
- **Backend**: Python with Flask
- **Database**: PostgreSQL
- **Containerization**: Docker and Docker Compose
- **Messaging**: Kafka
- **Frontend**: Flask with Bootstrap and DataTables.js

### Supporting Technologies
- **Scheduling**: APScheduler
- **Geocoding**: OpenStreetMap API (via geopy and OSRM)
- **Email**: Python's SMTP library with local SMTP client (Proton)
- **Web Scraping**: BeautifulSoup/Scrapy for 116117.de integration

## 2. System Architecture

### Microservice Structure
The system follows a domain-driven microservice architecture:

```
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ Patient       │   │ Therapist     │   │ Matching      │
│ Service       │   │ Service       │   │ Service       │
└───────────────┘   └───────────────┘   └───────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                    ┌───────────────┐
                    │ Kafka         │
                    │ Message Bus   │
                    └───────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ Communication │   │ Geocoding     │   │ Scraping      │
│ Service       │   │ Service       │   │ Service       │
└───────────────┘   └───────────────┘   └───────────────┘
```

### Communication Patterns
A **hybrid approach** combining:
- **REST APIs**: For direct queries and user-facing operations
- **Kafka Events**: For asynchronous processes and event broadcasting

## 3. Database Strategy

### Structure
- **Single PostgreSQL Instance** with separate schemas per service:
  - `patient_service`
  - `therapist_service`
  - `matching_service`
  - `communication_service`
  - `geocoding_service`
  - `scraping_service`

### Configuration
- PgBouncer for connection pooling
- Alembic for schema migrations
- Service-specific migration scripts

## 4. Messaging Configuration

### Kafka Topics

**Event Topics**:
- `patient-events`: Patient creation, updates, deletions
- `therapist-events`: Therapist profile changes, availability updates
- `matching-events`: New matches, status changes, rejection events
- `communication-events`: Email sent, response received, call scheduled

**Command Topics**:
- `email-commands`: Requests to send emails
- `scraping-commands`: Requests to initiate scraping jobs
- `geocoding-requests`: Requests for distance calculations

### Event Schema
```json
{
  "eventId": "uuid",
  "eventType": "patient.created",
  "version": "1.0",
  "timestamp": "ISO-8601",
  "producer": "patient-service",
  "payload": { /* domain-specific data */ }
}
```

### When to Use REST vs Kafka

**Use Kafka for**:
- Event notifications
- Asynchronous operations
- Multi-service broadcasting
- Workflow triggers

**Use REST for**:
- Data retrieval/queries
- User-facing operations
- Synchronous validation
- Simple CRUD operations

## 5. External API Integration

### OpenStreetMap Integration
- **Libraries**: geopy with Nominatim for geocoding, OSRM for routing
- **Caching**: PostgreSQL-based cache with expiration timestamps
- **Rate Limiting**: Token bucket algorithm (1 request/second)
- **Resilience**: Circuit breaker pattern and fallback mechanisms

### Implementation
- Dedicated `geocoding_service` microservice
- REST API endpoints for address validation and travel time calculation
- Kafka consumer for batch processing location tasks

## 6. Scheduled Tasks

### APScheduler Implementation
- Persistent job store in PostgreSQL
- Background scheduler mode in each service that needs scheduling
- UTC timezone standardization

### Key Scheduled Tasks
- Daily therapist scraping integration
- Weekly email batching for therapists
- Cleanup of outdated geocoding cache entries
- Status updates for stale placement requests

### Failure Handling
- Maximum retry configuration per job type
- Dead letter storage for failed jobs
- Alert mechanism for critical failures

## 7. Email System

### SMTP Configuration
- Use Proton's local SMTP client for sending emails
- MailHog for local development email testing

### Template System
- Jinja2 templates (same as Flask views)
- Version-controlled templates with dynamic content areas

### Queue Management
- Dedicated email queue in Kafka (`email-commands`)
- Batch processing for same-therapist emails
- Frequency limits enforcement (max 1 email per therapist per week)

## 8. Development Workflow

### Docker Compose Configuration
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_PASSWORD: password
      POSTGRES_USER: user
      POSTGRES_DB: therapy_platform
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  zookeeper:
    image: confluentinc/cp-zookeeper:latest
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
    
  kafka:
    image: confluentinc/cp-kafka:latest
    depends_on:
      - zookeeper
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    ports:
      - "9092:9092"

  # Service examples
  patient-service:
    build: ./patient-service
    depends_on:
      - postgres
      - kafka
    environment:
      DB_URI: postgresql://user:password@postgres:5432/therapy_platform
      KAFKA_BOOTSTRAP_SERVERS: kafka:9092
    ports:
      - "8001:8000"
  
  # Other services follow same pattern
  
  # For local email testing
  mailhog:
    image: mailhog/mailhog
    ports:
      - "1025:1025"  # SMTP server
      - "8025:8025"  # Web UI

volumes:
  postgres_data:
```

### Project Structure
```
/therapy-platform
  /shared                   # Shared code
    /models                 # Common data models
    /utils                  # Utility functions
    /kafka                  # Kafka utils
    /api                    # API utilities
  
  /patient-service          # One directory per microservice
    /api                    # REST API endpoints
    /models                 # Service-specific models
    /events                 # Kafka producers/consumers
    /templates              # HTML templates
    /static                 # CSS, JS, etc.
    Dockerfile
  
  /therapist-service        # Similar structure
  # Other services...
  
  docker-compose.yml        # Main Docker Compose file
  README.md
```

## 9. Deployment Strategy

### Service Startup Order
1. PostgreSQL
2. Zookeeper & Kafka
3. Essential services (patient, therapist)
4. Supporting services (geocoding, communication)
5. Frontend/API gateway

### Volume Management
- PostgreSQL data: `/var/lib/postgresql/data`
- Kafka data: `/var/lib/kafka/data`
- Application logs: `/var/log/therapy-platform`
- Email templates: `/app/templates` (bind mount for easy updates)

### Environment Configuration
- `.env` file for local development
- Environment variables structured by service and function

## 10. Monitoring & Debugging

### Logging Strategy
- Structured JSON logging with Python's `structlog`
- Standard fields for all log entries
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

### Health Checks
- `/health/liveness`: Basic application up check
- `/health/readiness`: Dependencies (DB, Kafka) are available
- `/health/status`: Detailed service status with metrics

### Error Tracking
- Centralized error handling with Flask error handlers
- Unique error codes for all error types
- Transaction IDs for request tracing

## 11. Web Scraping Implementation

### Architecture
- Dedicated scraping service for therapist data from 116117.de
- Daily scheduled updates
- Data validation and change detection

### Integration
- REST API to trigger scraping jobs
- Kafka events for scraping results
- Database updates for therapist information

## 12. Future Considerations

### Cloud Migration Path
- Container structure already suitable for Kubernetes
- State stored in database for resilience
- Environment variables for configuration

### Scalability
- Independent scaling of services
- Database partitioning approach
- Caching strategy for read-heavy operations

## 13. Code requirements
- All Python code should be conform with Flake8 including blank lines are not allowed to contain whitespaces and at the end a newline is required