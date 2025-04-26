# Psychotherapy Matching Platform - Technical Architecture

## 1. System Overview

The Psychotherapy Matching Platform is designed as a microservice-based system to facilitate the matching of patients with therapists in Germany. The architecture follows domain-driven design principles and is built to be stateless to allow for daily shutdown of Docker containers.

### 1.1 High-Level Architecture

```
┌────────────────────┐     ┌────────────────────┐     ┌────────────────────┐
│                    │     │                    │     │                    │
│  Frontend (SPA)    │────▶│   API Gateway      │────▶│  Microservices     │
│  German UI         │     │                    │     │                    │
│  (Future Multi-    │◀────│                    │◀────│                    │
│   lingual)         │     │                    │     │                    │
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
│                    │     │                    │     │                    │
└────────────────────┘     └────────────────────┘     └────────────────────┘
```

### 1.2 Design Principles

- **Domain-Driven Design**: Services organized around business domains
- **Stateless Architecture**: All services operate without session state
- **Database-Centered**: State maintained in database for resilience
- **Modular & Extensible**: Components can be upgraded individually
- **Security-First**: GDPR compliance built into the design
- **Future-Ready**: Prepared for cloud migration

## 2. Microservice Architecture

### 2.1 Core Domain Services

#### 2.1.1 Patient Service
- **Responsibility**: Manage all patient-related data and operations
- **Key Functions**:
  - Patient profile CRUD operations
  - Medical history tracking
  - Preference management
  - Availability management
  - Status tracking
- **State Management**: All patient state stored in database

#### 2.1.2 Therapist Service
- **Responsibility**: Manage therapist data and availability
- **Key Functions**:
  - Therapist profile CRUD operations
  - Availability tracking
  - Specialty and qualification management
  - Blocking/unblocking therapists
  - Contact history
- **State Management**: All therapist state stored in database

#### 2.1.3 Matching Service
- **Responsibility**: Core business logic for matching patients to therapists
- **Key Functions**:
  - Implement matching algorithm
  - Filter therapists based on criteria
  - Manage placement requests
  - Track matching history
  - Prioritize therapist contacts
- **State Management**: All matching state stored in database

#### 2.1.4 Communication Service
- **Responsibility**: Handle all external communications
- **Key Functions**:
  - Email template management
  - Email composition and dispatch
  - Phone call scheduling
  - Communication history tracking
  - Batch processing of communications
- **State Management**: 
  - Email queue in database
  - Communication logs in database

### 2.2 Supporting Services

#### 2.2.1 Geocoding Service
- **Responsibility**: Handle location-based operations
- **Key Functions**:
  - Address validation
  - Distance calculation
  - Travel time estimation
  - Integration with OpenStreetMap API
- **State Management**: Cache results in database for performance

#### 2.2.2 Data Acquisition Service
- **Responsibility**: Source and update therapist data
- **Key Functions**:
  - Web scraping from 116117.de
  - Data validation and enrichment
  - Change detection
  - Scraping job management
- **State Management**:
  - Scraping progress in database
  - Change logs in database

#### 2.2.3 Scheduling Service
- **Responsibility**: Manage time-sensitive operations
- **Key Functions**:
  - Contact frequency management
  - Therapist availability window tracking
  - Schedule optimization
  - Communication timing management
- **State Management**: All schedules stored in database

#### 2.2.4 Analytics Service
- **Responsibility**: Provide insights and reporting
- **Key Functions**:
  - Success rate tracking
  - Process efficiency metrics
  - Report generation
  - Trend analysis
- **State Management**: Aggregated metrics stored in database

## 3. Data Flow

### 3.1 Primary Workflows

#### 3.1.1 Patient Registration Flow
1. Frontend collects patient data
2. Patient Service validates and stores data
3. Matching Service initiates matching process

#### 3.1.2 Therapist Matching Flow
1. Matching Service queries Therapist Service for candidates
2. Geocoding Service calculates distances
3. Matching Service applies filters and creates placement requests
4. Communication Service notifies therapists

#### 3.1.3 Communication Flow
1. Communication Service batches requests by therapist
2. Email templates populated with patient data
3. Emails queued in database
4. Emails sent and responses tracked

#### 3.1.4 Therapist Data Update Flow
1. Data Acquisition Service scrapes 116117.de
2. Changes detected and logged
3. Therapist Service updates therapist data
4. Notifications generated for manual verification

## 4. Database Schema

### 4.1 Core Entities

- **patients**: Patient profiles and medical information
- **therapists**: Therapist profiles and availability
- **placement_requests**: Matching attempts between patients and therapists
- **communications**: Record of all communications
- **phone_calls**: Scheduled and completed phone calls
- **emails**: Email content and tracking

### 4.2 Supporting Entities

- **geocoding_cache**: Cached location data
- **scraping_jobs**: Web scraping job tracking
- **system_settings**: Configuration parameters
- **audit_logs**: System activity for compliance

## 5. Stateless Implementation Strategy

### 5.1 Statelessness Principles
- No session state in application memory
- All state persisted to database
- Idempotent API operations
- Transaction-based processing

### 5.2 Service-Specific Considerations

#### 5.2.1 Communication Service
- Email dispatch jobs stored in database
- Status tracking with retry capability
- Transaction logs for email sending

#### 5.2.2 Data Acquisition Service
- Scraping progress checkpoints
- Resumable operations
- Complete/incomplete status tracking

#### 5.2.3 Scheduling Service
- Next execution time stored in database
- Job status tracking
- Missed execution detection on startup

### 5.3 Daily Shutdown Procedure
1. Graceful shutdown signals to all services
2. Completion of in-progress transactions
3. Database connection closure
4. System shutdown
5. On restart: recovery procedures for interrupted operations

## 6. Security and Compliance

### 6.1 Data Protection
- GDPR-compliant data handling
- Encryption of sensitive data
- Role-based access control
- Audit logging

### 6.2 Authentication & Authorization
- Secure credential storage
- Fine-grained permissions
- Session management

## 7. Deployment Strategy

### 7.1 Local Deployment
- Container orchestration for local services
- Persistent storage for database
- Configuration via environment variables
- Automated build and deployment scripts

### 7.2 Future Cloud Migration Path
- Cloud-ready service design
- Platform-independent storage abstraction
- Scalability considerations
- Multi-region deployment capability

## 8. Monitoring and Observability

### 8.1 Logging Strategy
- Structured logging
- Centralized log storage
- Log levels for different environments

### 8.2 Metrics
- Service health metrics
- Business process metrics
- Performance monitoring

## 9. Future Expansion Considerations

### 9.1 Multilingual Support
- Internationalization framework in frontend
- Translation management system
- Locale-specific formatting

### 9.2 API Expansion
- Public API for integration partners
- Webhook capabilities
- OAuth for third-party access

### 9.3 AI/ML Integration
- Matching algorithm improvements
- Patient-therapist compatibility scoring
- Prediction of therapy success likelihood