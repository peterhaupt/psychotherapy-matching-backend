# Technical Architecture

## System Overview

Microservice architecture for bundle-based therapy matching with progressive filtering and parallel search capabilities.

## Architecture Diagram

```
┌─────────────┐    ┌──────────────┐    ┌───────────────────────────┐
│   Frontend  │───▶│  API Gateway │───▶│     Microservices         │
└─────────────┘    └──────────────┘    │ - Patient Service         │
                                       │ - Therapist Service       │
                                       │ - Matching Service (v2)   │
                                       │ - Communication Service   │
                                       │ - Geocoding Service       │
                                       └───────────┬───────────────┘
                                                   │
                   ┌───────────────────────────────┼───────────────┐
                   │                               │               │
            ┌──────▼──────┐         ┌──────────────▼─────┐   ┌─────▼──────┐
            │ PostgreSQL  │         │      Kafka         │   │  External  │
            │ (Schemas)   │         │ (Event Streaming) │   │  Services  │
            └─────────────┘         └────────────────────┘   └────────────┘
```

## Technology Stack

- **Backend**: Python 3.11, Flask, SQLAlchemy
- **Database**: PostgreSQL with PgBouncer
- **Messaging**: Kafka
- **Containerization**: Docker
- **External**: OpenStreetMap, SMTP, 116117.de scraper

## Service Architecture Updates

### Matching Service v2
**New Responsibilities:**
- Bundle creation with progressive filtering
- Cooling period management
- Parallel search orchestration
- Conflict resolution
- Therapist preference learning

**Key Algorithms:**
```python
def create_bundle(patient_search):
    # 1. Get eligible therapists (not in cooling)
    # 2. Apply hard constraints (distance, exclusions)
    # 3. Progressive filtering by preferences
    # 4. Sort by patient wait time
    # 5. Select 3-6 patients per therapist
```

### Communication Service Integration
- Receives bundle composition from Matching Service
- Sends individual emails (no bundle logic)
- Tracks responses and notifies Matching Service
- Matching Service updates cooling periods

## Data Model Updates

### New Tables
```sql
-- Patient Search Management
platzsuche (
  id, patient_id, status, 
  excluded_therapists[], total_requested_contacts
)

-- Therapist Inquiry Bundle
therapeutenanfrage (
  id, therapist_id, bundle_size,
  response_type, accepted_count
)

-- Bundle Composition
therapeut_anfrage_patient (
  therapeutenanfrage_id, platzsuche_id,
  patient_id, position_in_bundle, status
)
```

### Enhanced Models
- **Patient**: +travel preferences, detailed availability
- **Therapist**: +cooling dates, preferences, working hours

## Event Architecture

### New Event Types
```json
{
  "eventType": "bundle.created",
  "payload": {
    "bundle_id": "uuid",
    "therapist_id": 123,
    "patient_ids": [1,2,3]
  }
}
```

**Bundle Events:**
- `bundle.created`
- `bundle.sent`
- `bundle.response_received`
- `search.updated`
- `cooling.period_started`

## API Design (v2)

### Endpoints
```
# Search Management
POST   /api/v2/patient-searches
GET    /api/v2/patient-searches/{id}
POST   /api/v2/patient-searches/{id}/contact-requests

# Bundle Operations  
POST   /api/v2/bundles/create
GET    /api/v2/bundles/{id}
PUT    /api/v2/bundles/{id}/response

# Analytics
GET    /api/v2/analytics/bundle-efficiency
GET    /api/v2/analytics/therapist-preferences
```

## Feature Flag Architecture

```python
FEATURE_FLAGS = {
    'bundle_matching': {
        'enabled': True,
        'rollout_percentage': 50,
        'override_users': ['admin']
    }
}
```

## Performance Considerations

### Caching Strategy
- Therapist eligibility cache (5 min TTL)
- Distance calculation cache (30 days)
- Bundle composition cache (1 hour)

### Database Optimization
- Indexes on search status, cooling dates
- Materialized views for therapist preferences
- Partitioning for historical data

## Security & Compliance

- GDPR-compliant data handling
- Audit logging for all bundle operations
- Role-based access (staff vs admin)
- Encrypted PII at rest

## Deployment Strategy

### Container Orchestration
- Feature-flagged deployment
- Blue-green deployment option
- Database migration automation
- Rollback capabilities

### Monitoring
- Bundle creation performance
- API response times
- Cooling period violations
- Success rate tracking

## Integration Points

### Internal Services
- Centralized configuration
- Shared event schemas
- Common database utilities
- Unified error handling

### External Systems
- Cloud storage for scraper data
- SMTP for communications
- OpenStreetMap for geocoding
- Future: Insurance APIs