# Implementation Plan

Phased implementation approach for the Psychotherapy Matching Platform.

## Phase 1: Foundation (✅ Completed)

### Achievements
- Docker/PostgreSQL/Kafka infrastructure
- Core microservices (Patient, Therapist, Matching, Communication, Geocoding)
- Basic CRUD operations and event system
- Web scraping service (separate repository)

## Phase 2: Integration & Enhancement (✅ Completed)

### Achievements
- Email system with templates
- Phone call scheduling
- Geocoding with caching
- Centralized configuration
- Basic matching with simple placement requests

## Phase 3: Bundle-Based Matching System (🚧 Current - 3 weeks)

### Overview
Transform the current basic matching system into the bundle-based system described in business requirements.

### Week 1: Database Schema Updates

**New Tables:**
```sql
-- Patient search tracking
CREATE TABLE matching_service.platzsuche (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    excluded_therapists JSONB DEFAULT '[]',
    total_requested_contacts INTEGER DEFAULT 0
);

-- Bundle tracking
CREATE TABLE matching_service.therapeutenanfrage (
    id SERIAL PRIMARY KEY,
    therapist_id INTEGER NOT NULL,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_date TIMESTAMP,
    response_type VARCHAR(50),
    bundle_size INTEGER,
    accepted_count INTEGER DEFAULT 0
);

-- Bundle composition
CREATE TABLE matching_service.therapeut_anfrage_patient (
    id SERIAL PRIMARY KEY,
    therapeutenanfrage_id INTEGER NOT NULL,
    platzsuche_id INTEGER NOT NULL,
    patient_id INTEGER NOT NULL,
    position_in_bundle INTEGER,
    status VARCHAR(50) DEFAULT 'pending'
);
```

**Column Additions:**
```sql
-- Patient enhancements
ALTER TABLE patient_service.patients ADD COLUMN 
    max_travel_distance_km INTEGER DEFAULT 30,
    travel_mode VARCHAR(50) DEFAULT 'Auto',
    availability_schedule JSONB;

-- Therapist enhancements
ALTER TABLE therapist_service.therapists ADD COLUMN
    next_contactable_date DATE,
    preferred_diagnoses JSONB,
    age_min INTEGER,
    age_max INTEGER,
    gender_preference VARCHAR(50),
    working_hours JSONB;
```

### Week 2: Bundle Algorithm Implementation

**Core Components:**

1. **Bundle Creation Service** (`matching_service/algorithms/bundle_creator.py`):
   ```python
   def create_bundles_for_all_therapists():
       # 1. Get all contactable therapists
       # 2. For each therapist, apply progressive filtering
       # 3. Create bundles of 3-6 patients
       # 4. Update cooling periods
   ```

2. **Progressive Filtering** (`matching_service/algorithms/filters.py`):
   - Hard constraints (distance, exclusions, gender)
   - Soft preferences (diagnosis, age, availability)
   - Sorting by patient wait time

3. **Conflict Resolution** (`matching_service/algorithms/conflict_resolver.py`):
   - Handle multiple acceptances
   - Reassign patients
   - Notify affected therapists

4. **API Updates** (modify existing endpoints):
   ```
   POST /api/placement-requests/bulk    # Create bundles
   GET  /api/placement-requests/bundles # View bundles
   PUT  /api/placement-requests/bundle-response # Record responses
   ```

### Week 3: Testing & Refinement

**Testing Strategy:**
1. **Unit Tests**:
   - Bundle algorithm with various scenarios
   - Progressive filtering logic
   - Cooling period calculations

2. **Integration Tests**:
   - Full flow from patient search to bundle creation
   - Email generation with correct templates
   - Phone call scheduling after 7 days

3. **Load Testing**:
   - 100+ patients, 50+ therapists
   - Performance targets: <2s bundle creation

**Test Data Generation:**
```python
# scripts/generate_test_data.py
- Create patients with varied preferences
- Create therapists with different availability
- Simulate various response patterns
```

### Success Criteria
- [x] Database schema updated
- [ ] Bundle algorithm creates appropriate groups
- [ ] Cooling periods enforced correctly
- [ ] Email templates use bundle data
- [ ] Tests pass with good coverage
- [ ] Performance meets targets

## Phase 4: Web Interface (Planned - 4 weeks)

### Week 1-2: Core UI
- Patient search dashboard
- Bundle creation interface
- Response recording

### Week 3-4: Advanced Features
- Real-time updates
- Conflict resolution UI
- Analytics dashboard

### Technical Stack
- React with TypeScript
- Material-UI or similar
- WebSocket for real-time updates

## Phase 5: Production Preparation (Planned - 2 weeks)

### Infrastructure
- Production Docker configuration
- Database backup strategy
- Monitoring setup (Prometheus/Grafana)
- Log aggregation

### Security
- Authentication implementation
- API rate limiting
- Data encryption
- Security audit

### Documentation
- API documentation
- Deployment guide
- User manual

## Phase 6: Advanced Features (Future)

### Machine Learning
- Success prediction models
- Preference learning from acceptance patterns
- Optimal bundle size prediction

### Integrations
- Insurance system APIs
- Hospital referral systems
- Mobile applications

## Key Decisions for Early Development

### What We're NOT Doing Yet:
- ❌ API versioning (no existing clients)
- ❌ Feature flags (no users to roll out to)
- ❌ Complex rollback procedures (can recreate database)
- ❌ Backward compatibility (greenfield project)

### What We ARE Doing:
- ✅ Direct implementation of new features
- ✅ Comprehensive testing with mock data
- ✅ Clear separation of basic vs bundle matching
- ✅ Focus on core business logic first

## Development Workflow

1. **Branch Strategy**:
   - `main`: Stable code
   - `feature/bundle-matching`: Current work
   - Direct commits during early development

2. **Database Changes**:
   - Create migrations
   - Test locally
   - Reset database as needed

3. **Testing Approach**:
   - Write tests alongside features
   - Use mock data extensively
   - Manual testing with realistic scenarios

## Risks & Mitigation

### Technical Risks
- **Algorithm complexity**: Start simple, iterate based on results
- **Performance**: Profile early, optimize as needed
- **Data quality**: Validate all inputs, handle edge cases

### Business Risks
- **Requirements clarity**: Regular reviews of bundle logic
- **User acceptance**: Early demos with stakeholders

## Definition of Done

A feature is complete when:
- [ ] Code is written and reviewed
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Documentation updated
- [ ] Manual testing completed
- [ ] Performance acceptable