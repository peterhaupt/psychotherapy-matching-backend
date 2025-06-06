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

### Week 1: Database Schema Updates ✅ COMPLETED

**Achievements:**
- Created comprehensive migration for bundle system
- Added new tables for patient search and bundle tracking
- Extended therapist model with preferences
- Applied migration to database

**Important Decision:** All database fields use German names for consistency

### Week 2: Bundle Algorithm Implementation 🔄 CURRENT

**Day 1-2: Model Updates**
1. ✅ Rename English fields to German:
   ```sql
   -- Migration bcfc97d0f1h1
   next_contactable_date → naechster_kontakt_moeglich
   preferred_diagnoses → bevorzugte_diagnosen
   age_min → alter_min
   age_max → alter_max
   gender_preference → geschlechtspraeferenz
   working_hours → arbeitszeiten
   ```

2. 📋 Update Therapist model with new fields:
   ```python
   # therapist_service/models/therapist.py
   naechster_kontakt_moeglich = Column(Date)
   bevorzugte_diagnosen = Column(JSONB)
   alter_min = Column(Integer)
   alter_max = Column(Integer)
   geschlechtspraeferenz = Column(String(50))
   arbeitszeiten = Column(JSONB)
   ```

3. 📋 Create new bundle models:
   ```python
   # matching_service/models/bundle.py
   class Platzsuche(Base):
       # Patient search tracking
   
   class Therapeutenanfrage(Base):
       # Therapist inquiry (bundle)
   
   class TherapeutAnfragePatient(Base):
       # Bundle composition
   ```

**Day 3-4: Core Algorithm**
1. 📋 Bundle Creation Service (`matching_service/algorithms/bundle_creator.py`):
   ```python
   def erstelle_buendel_fuer_alle_therapeuten():
       # 1. Hole kontaktierbare Therapeuten
       # 2. Wende progressive Filterung an
       # 3. Erstelle Bündel mit 3-6 Patienten
       # 4. Aktualisiere Abkühlungszeiten
   ```

2. 📋 Progressive Filtering (`matching_service/algorithms/filters.py`):
   - Harte Bedingungen (Entfernung, Ausschlüsse, Geschlecht)
   - Weiche Präferenzen (Diagnose, Alter, Verfügbarkeit)
   - Sortierung nach Wartezeit

**Day 5: API & Integration**
1. 📋 API Updates:
   ```
   POST /api/platzsuchen           # Neue Patientensuche starten
   POST /api/therapeutenanfragen   # Bündel erstellen
   PUT  /api/therapeutenanfragen/{id}/antwort # Antwort erfassen
   ```

2. 📋 Communication Service Integration:
   - Bundle data passed correctly to email templates
   - Response tracking updates bundle status

### Week 3: Testing & Refinement 📋 PLANNED

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
- Patienten mit verschiedenen Präferenzen
- Therapeuten mit unterschiedlicher Verfügbarkeit
- Simulation verschiedener Antwortmuster
```

### Success Criteria
- ✅ Database schema updated with German field names
- [ ] Bundle algorithm creates appropriate groups
- [ ] Abkühlungsphase correctly enforced
- [ ] Email templates use bundle data
- [ ] Tests pass with good coverage
- [ ] Performance meets targets

## German Naming Convention Guidelines

### Database Fields
- **Use German names** for all new fields
- **Match existing patterns**: `vorname`, `nachname`, `strasse`
- **Compound words**: Use underscores `telefonische_erreichbarkeit`
- **Keep technical terms**: `id`, `status`, `created_at`

### Model Attributes
- Match database field names exactly
- No translation layer between DB and models

### API Endpoints
- Can use English for REST conventions: `/api/therapists`
- Request/response fields should match model fields (German)

### Examples
✅ Correct:
```python
bevorzugte_diagnosen = Column(JSONB)
naechster_kontakt_moeglich = Column(Date)
```

❌ Incorrect:
```python
preferred_diagnoses = Column(JSONB)  # English
next_contactable_date = Column(Date) # English
```

## Phase 4: Web Interface (Planned - 4 weeks)

### Week 1-2: Core UI
- Patient search dashboard (Patientensuche)
- Bundle creation interface (Bündelerstellung)
- Response recording (Antworterfassung)

### Week 3-4: Advanced Features
- Real-time updates
- Conflict resolution UI
- Analytics dashboard

### Technical Stack
- React with TypeScript
- Material-UI components
- German UI labels
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
- API documentation (with German field names)
- Deployment guide
- User manual (German)

## Key Decisions for Development

### Naming Conventions
- ✅ **German field names** throughout the system
- ✅ **Consistent with existing codebase**
- ✅ **No mixing of languages in database schema**

### What We're NOT Doing Yet:
- ❌ API versioning (no existing clients)
- ❌ Feature flags (no users to roll out to)
- ❌ Complex rollback procedures (can recreate database)
- ❌ Backward compatibility (greenfield project)

### What We ARE Doing:
- ✅ Consistent German naming
- ✅ Direct implementation of new features
- ✅ Comprehensive testing with mock data
- ✅ Clear separation of basic vs bundle matching

## Development Workflow

1. **Current Sprint**:
   - Apply German field renaming migration
   - Update models with new fields
   - Implement bundle algorithm
   - Test with realistic German data

2. **Database Changes**:
   - Create migrations with German names
   - Test locally
   - Document all fields in German

3. **Code Style**:
   - Comments in English (for international team)
   - Field names in German (domain consistency)
   - Variable names in English (programming convention)

## Definition of Done

A feature is complete when:
- [ ] Code uses German field names consistently
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Documentation updated (with German terminology)
- [ ] Manual testing completed
- [ ] Performance acceptable