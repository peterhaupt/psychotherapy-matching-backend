# Technical Architecture

## Overview

The Psychotherapy Matching Platform is designed as a microservice-based system to facilitate matching patients with therapists in Germany. This document outlines the technical architecture, design principles, and implementation approach.

## 1. System Architecture

### 1.1 High-Level Architecture

```
┌────────────────────┐     ┌────────────────────┐     ┌────────────────────┐
│                    │     │                    │     │                    │
│  Frontend          │────▶│   API Gateway      │────▶│  Microservices     │
│                    │     │                    │     │                    │
└────────────────────┘     └────────────────────┘     └────────────────────┘
                                                               │
                                                               │
                                                               ▼
┌────────────────────┐     ┌────────────────────┐     ┌────────────────────┐
│                    │     │                    │     │                    │
│  External Services │◀────│  Persistent        │◀────│  Message Queue     │
│  - OpenStreetMap   │     │  Storage           │     │                    │
│  - SMTP            │     │  - Database        │     │                    │
│  - 116117.de       │     │  - File Storage    │     │                    │
└────────────────────┘     └────────────────────┘     └────────────────────┘
```

### 1.2 Design Principles

- **Domain-Driven Design**: Services organized around business domains
- **Stateless Architecture**: Services operate without session state
- **Database-Centered**: State maintained in database for resilience
- **Modular & Extensible**: Components can be upgraded individually
- **Security-First**: GDPR compliance built into the design

## 2. Technology Stack

- **Backend**: Python 3.11 with Flask
- **Database**: PostgreSQL
- **Containerization**: Docker and Docker Compose
- **Messaging**: Kafka
- **API**: REST with Flask-RESTful
- **Geocoding**: OpenStreetMap API
- **Email**: Python's SMTP library with local client

## 3. Microservice Components

### 3.1 Core Services

#### Patient Service
- Patient profile management
- Medical information handling
- Availability and preference tracking
- Patient state management

#### Therapist Service
- Therapist profile management
- Availability tracking
- Specialty and qualification handling
- Contact history tracking

#### Matching Service
- Implementation of matching algorithm
- Placement request management
- Matching history tracking
- Prioritization handling

#### Communication Service
- Email template management
- Email dispatch and tracking
- Phone call scheduling
- Communication history tracking
- Batch processing

### 3.2 Supporting Services

#### Geocoding Service
- Address validation
- Distance calculation
- Travel time estimation
- Geocoding cache

#### Data Acquisition Service (Scraping)
- Web scraping from 116117.de
- Data validation and normalization
- Therapist data enrichment

## 4. Database Design

### 4.1 Schema Strategy

Single PostgreSQL database with separate schemas:
- `patient_service`
- `therapist_service`
- `matching_service`
- `communication_service`
- `geocoding_service`
- `scraping_service`

### 4.2 Schema Isolation

- Each microservice accesses only its own schema
- Cross-service data access via APIs, not direct DB access
- Shared database for development simplicity
- Designed for future separation if needed

### 4.3 Connection Management

- PgBouncer for connection pooling
- Session management via shared utilities
- Connection resilience patterns

## 5. Communication Patterns

### 5.1 Synchronous Communication

REST APIs used for:
- Direct queries
- User-facing operations
- Immediate feedback requirements
- Simple CRUD operations

### 5.2 Asynchronous Communication

Kafka used for:
- Event notifications
- Inter-service workflow triggers
- Background processes
- Eventual consistency

### 5.3 Event Schema

```json
{
  "eventId": "uuid",
  "eventType": "service.action",
  "version": "1.0",
  "timestamp": "ISO-8601",
  "producer": "service-name",
  "payload": {}
}
```

## 6. Resilience Patterns

### 6.1 Database Resilience

- Proper session management
- Transaction boundaries
- Error handling and rollbacks
- Connection pooling

### 6.2 Messaging Resilience

- Robust Kafka producer with reconnection
- Message queuing during outages
- At-least-once delivery semantics
- Message persistency

### 6.3 API Resilience

- Circuit breaker patterns
- Request validation
- Rate limiting
- Appropriate error responses

## 7. Containerization

### 7.1 Docker Configuration

- One container per microservice
- Shared volume for code during development
- Environment variables for configuration
- Health checks for service dependencies

### 7.2 Container Orchestration

- Docker Compose for local development
- Service dependency management
- Volume mapping for persistence
- Network configuration

## 8. Security Considerations

### 8.1 Data Protection

- GDPR-compliant data handling
- Minimized data collection
- Appropriate data retention policies
- Secure data transmission

### 8.2 Authentication & Authorization

- Role-based access control
- Proper credential management
- Session security
- API security

## 9. External Integrations

### 9.1 OpenStreetMap Integration

- Geocoding for addresses
- Distance calculations
- Travel time estimation
- Results caching

### 9.2 Email Integration

- SMTP for email sending
- Template-based email generation
- Delivery tracking
- Response handling

### 9.3 Web Scraping

- 116117.de data extraction
- Rate limiting and respectful access
- Data normalization
- Change detection

## 10. Deployment Strategy

### 10.1 Development Environment

- Local Docker Compose setup
- Shared database instance
- Volume mounts for live code updates
- Development tools

### 10.2 Future Production Environment

- Cloud-ready service design
- Kubernetes deployment options
- Multi-region considerations
- Scalability planning