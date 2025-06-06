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
- Scraper integration via cloud storage
- Email batching and phone call scheduling
- Centralized configuration
- Comprehensive documentation
- Testing framework

## Phase 3: Bundle-Based Matching System (🚧 Current - 4 weeks)

### Week 1: Database Schema Updates

**New Tables:**
```sql
-- Patient search management
CREATE TABLE matching_service.platzsuche (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    excluded_therapists JSONB DEFAULT '[]',
    total_requested_contacts INTEGER DEFAULT 0
);

-- Therapist inquiry bundles
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

**Column Updates:**
```sql
-- Patient updates
ALTER TABLE patient_service.patients ADD COLUMN 
    max_travel_distance_km INTEGER,
    travel_mode VARCHAR(50),
    availability_schedule JSONB;

-- Therapist updates  
ALTER TABLE therapist_service.therapists ADD COLUMN
    next_contactable_date DATE,
    last_contact_date DATE,
    preferred_diagnoses JSONB,
    age_min INTEGER,
    age_max INTEGER;
```

### Week 2-3: Service Logic & API Implementation

**Matching Service v2:**
- Bundle creation algorithm with progressive filtering
- Cooling period enforcement via `next_contactable_date`
- Parallel bundle support with conflict resolution
- New API endpoints with versioning:
  ```
  # v1 endpoints (maintain for compatibility)
  GET/POST /api/placement-requests
  
  # v2 endpoints (new bundle system)
  POST   /api/v2/patient-searches
  POST   /api/v2/bundles/create
  PUT    /api/v2/bundles/{id}/response
  GET    /api/v2/analytics/bundle-efficiency
  ```

**Communication Service Updates:**
- Maintain existing email/phone endpoints
- Remove bundle logic (handled by Matching Service)
- Add response notification to Matching Service

**Feature Flags:**
```python
FEATURE_FLAGS = {
    'bundle_matching': {
        'enabled': True,
        'rollout_percentage': 50,
        'override_users': ['admin']
    }
}
```

### Week 4: Testing & Deployment

**Testing Strategy:**
- Unit tests for bundle algorithm
- Integration tests for complete flow
- Performance tests (target: <2s bundle creation)
- UAT with staff using feature flags

**Deployment & Cutover:**
1. Deploy with feature flags disabled
2. Run parallel with old system
3. Gradual rollout by percentage
4. Monitor key metrics
5. Full cutover after validation

**Rollback Plan:**
```sql
-- Database rollback
DROP TABLE IF EXISTS matching_service.therapeut_anfrage_patient;
DROP TABLE IF EXISTS matching_service.therapeutenanfrage;
DROP TABLE IF EXISTS matching_service.platzsuche;
-- Revert column additions...

-- Code rollback
-- 1. Disable feature flags
-- 2. Revert to previous release tag
-- 3. Clear caches
```

### Success Criteria
- [ ] All models implemented
- [ ] APIs returning correct data  
- [ ] Cooling periods enforced
- [ ] Performance <2s for bundle creation
- [ ] Staff can create bundles
- [ ] Parallel bundles working

## Phase 4: Web Interface (Planned - 4 weeks)

### Core Features
- Patient search management UI
- Bundle creation interface
- Response recording
- Cooling period visualization
- Conflict resolution UI

### Technical Stack
- React/TypeScript frontend
- Material-UI components
- State management (Redux/Context)
- Real-time updates

## Phase 5: Production Readiness (Planned - 2 weeks)

### Performance
- Query optimization
- Caching implementation
- Load testing

### Security
- Authentication/authorization
- Data encryption
- Security audit

### Operations
- Monitoring setup
- Alert configuration
- Backup procedures
- Documentation completion

### Post-Migration Monitoring (First Month)
**Week 1-2:**
- Daily monitoring of bundle creation
- Response rate tracking
- Bug fixes for urgent issues

**Week 3-4:**
- Algorithm optimization based on data
- UI enhancements from feedback
- Deprecate old placement request endpoints

**Month 2:**
- Remove old models and code
- Analyze bundle effectiveness
- Plan next features

## Phase 6: Advanced Features (Future)

### Intelligence
- ML-based matching optimization
- Success prediction
- Preference learning

### Integration
- Insurance system APIs
- Hospital discharge systems
- Mobile applications

## Risk Mitigation

### Technical Risks
- **Algorithm performance**: Pre-calculate eligible therapists, use caching
- **Data conflicts**: Database locking, UI for manual resolution
- **Migration failures**: Comprehensive rollback scripts ready

### Business Risks
- **Staff adoption**: Hands-on training, gradual rollout
- **Therapist confusion**: Clear communication templates
- **Patient expectations**: Transparent process documentation

### Monitoring During Migration
- API response times
- Bundle creation success rate
- Cooling period violations
- Staff productivity metrics
- Database query performance

## Overall MVP Success Metrics
- [ ] Placement time <30 days average
- [ ] >20% therapist acceptance rate
- [ ] System handles 100+ concurrent searches
- [ ] Staff productivity improved 50%
- [ ] Zero data loss during migration
- [ ] Backward compatibility maintained