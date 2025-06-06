# Migration Plan: From Simple Placement Requests to Bundle-Based Matching

## Executive Summary

This document outlines the migration from the current simple placement request system to a sophisticated bundle-based matching system. The migration will transform how Curavani matches patients with therapists, introducing patient searches (Platzsuche), therapist inquiries (Therapeutenanfrage), cooling periods, and intelligent bundling.

**Migration Duration**: 3-4 weeks  
**Risk Level**: Low (no production data)  
**Backward Compatibility**: Maintained during transition

## Current State Analysis

### Existing System
- **Simple Model**: Direct 1:1 placement requests between patients and therapists
- **No Bundling**: Each request is handled individually
- **No Cooling Periods**: Therapists can be contacted repeatedly
- **Limited Tracking**: Basic status tracking (open, in progress, rejected, accepted)
- **Manual Process**: Staff manually create individual placement requests

### Existing Models
```
PlacementRequest
├── patient_id (FK)
├── therapist_id (FK)
├── status (enum)
├── created_at
├── response
└── notes
```

### Current Workflow
1. Staff identifies potential therapist for patient
2. Creates single placement request
3. Sends individual email
4. Tracks single response

## Target State Description

### New System Features
- **Patient Searches**: Long-running searches tracking entire patient journey
- **Bundled Inquiries**: 3-6 patients per therapist contact
- **Cooling Periods**: 4-week pause after any therapist response
- **Contact Tracking**: Track all contact attempts per search
- **Intelligent Matching**: Algorithm-based bundle creation
- **Parallel Processing**: Patients in multiple bundles simultaneously

### New Models
```
Platzsuche (Patient Search)
├── patient_id (FK)
├── status (active|successful|abandoned)
├── excluded_therapists
└── total_requested_contacts

Therapeutenanfrage (Therapist Inquiry)
├── therapist_id (FK)
├── sent_date
├── response_type
├── bundle_size
└── accepted_count

TherapeutAnfragePatient (Bundle Composition)
├── therapeutenanfrage_id (FK)
├── platzsuche_id (FK)
├── patient_id (FK)
├── position_in_bundle
└── status (pending|accepted|rejected)
```

## Migration Phases

### Phase 0: Preparation (2 days)

#### Tasks
1. **Documentation Updates**
   - Update TERMINOLOGY.md with new German terms
   - Create API specification for new endpoints
   - Document staff workflows
   - Update business requirements

2. **Development Environment**
   - Create feature flags for new system
   - Set up parallel testing environment
   - Configure logging for migration tracking

#### Deliverables
- Updated documentation
- Feature flag configuration
- Migration tracking setup

### Phase 1: Database Schema Updates (3 days)

#### Tasks
1. **Create New Tables**
   ```sql
   -- New tables for patient search management
   CREATE TABLE matching_service.platzsuche (
       id SERIAL PRIMARY KEY,
       patient_id INTEGER NOT NULL,
       status VARCHAR(50) DEFAULT 'active',
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       success_date TIMESTAMP,
       excluded_therapists JSONB DEFAULT '[]',
       total_requested_contacts INTEGER DEFAULT 0
   );

   CREATE TABLE matching_service.platzsuche_contact_request (
       id SERIAL PRIMARY KEY,
       platzsuche_id INTEGER NOT NULL,
       requested_count INTEGER NOT NULL,
       requested_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       created_by VARCHAR(255)
   );

   -- New tables for therapist inquiries
   CREATE TABLE matching_service.therapeutenanfrage (
       id SERIAL PRIMARY KEY,
       therapist_id INTEGER NOT NULL,
       created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       sent_date TIMESTAMP,
       sent_method VARCHAR(50),
       response_date TIMESTAMP,
       response_type VARCHAR(50),
       bundle_size INTEGER,
       accepted_count INTEGER DEFAULT 0,
       staff_notes TEXT
   );

   CREATE TABLE matching_service.therapeut_anfrage_patient (
       id SERIAL PRIMARY KEY,
       therapeutenanfrage_id INTEGER NOT NULL,
       platzsuche_id INTEGER NOT NULL,
       patient_id INTEGER NOT NULL,
       position_in_bundle INTEGER,
       status VARCHAR(50) DEFAULT 'pending',
       outcome_notes TEXT
   );
   ```

2. **Update Existing Tables**
   ```sql
   -- Patient table updates
   ALTER TABLE patient_service.patients 
   ADD COLUMN max_travel_distance_km INTEGER,
   ADD COLUMN travel_mode VARCHAR(50),
   ADD COLUMN availability_schedule JSONB,
   ADD COLUMN therapist_gender_preference VARCHAR(50),
   ADD COLUMN group_therapy_preference BOOLEAN DEFAULT FALSE;

   -- Therapist table updates
   ALTER TABLE therapist_service.therapists
   ADD COLUMN next_contactable_date DATE,
   ADD COLUMN last_contact_date DATE,
   ADD COLUMN preferred_diagnoses JSONB,
   ADD COLUMN age_min INTEGER,
   ADD COLUMN age_max INTEGER,
   ADD COLUMN gender_preference VARCHAR(50),
   ADD COLUMN group_therapy_preference BOOLEAN,
   ADD COLUMN working_hours JSONB;
   ```

3. **Create Indexes**
   ```sql
   CREATE INDEX idx_platzsuche_patient_id ON matching_service.platzsuche(patient_id);
   CREATE INDEX idx_platzsuche_status ON matching_service.platzsuche(status);
   CREATE INDEX idx_therapeutenanfrage_therapist_id ON matching_service.therapeutenanfrage(therapist_id);
   CREATE INDEX idx_therapeut_anfrage_patient_bundle ON matching_service.therapeut_anfrage_patient(therapeutenanfrage_id);
   ```

#### Deliverables
- Migration scripts
- Updated database schema
- Rollback scripts

### Phase 2: Model Implementation (4 days)

#### Tasks
1. **Create New Models**
   - `Platzsuche` model with methods for exclusion management
   - `PlatzucheContactRequest` for tracking contact requests
   - `Therapeutenanfrage` with response handling
   - `TherapeutAnfragePatient` for bundle composition

2. **Update Existing Models**
   - Enhance Patient model with new fields and validation
   - Enhance Therapist model with cooling period logic
   - Add helper methods for availability checking

3. **Deprecate Old Models**
   - Mark `PlacementRequest` as deprecated
   - Add warnings in code
   - Plan removal timeline

#### Deliverables
- New model classes
- Updated model documentation
- Deprecation warnings

### Phase 3: Service Logic Implementation (5 days)

#### Tasks
1. **Matching Service Updates**
   ```python
   # New methods needed
   - create_patient_search()
   - add_contact_request()
   - create_therapist_bundle()
   - enforce_cooling_period()
   - get_eligible_therapists()
   - compose_optimal_bundle()
   ```

2. **Bundle Creation Algorithm**
   - Implement progressive filtering
   - Distance calculation integration
   - Preference matching logic
   - Parallel bundle support

3. **Communication Service Updates**
   - Update email templates for multi-patient format
   - Modify email creation to accept bundle data
   - Ensure response tracking works with new models

4. **Event System Updates**
   - New events: `search.created`, `bundle.created`, `bundle.responded`
   - Update existing consumers
   - Add new event handlers

#### Deliverables
- Updated service code
- Algorithm implementation
- New event handlers

### Phase 4: API Implementation (3 days)

#### Tasks
1. **New API Endpoints**
   ```
   # Patient Search Management
   POST   /api/patient-searches
   GET    /api/patient-searches/{id}
   PUT    /api/patient-searches/{id}/exclude-therapist
   POST   /api/patient-searches/{id}/contact-requests

   # Bundle Management  
   POST   /api/therapist-bundles/create
   GET    /api/therapist-bundles/{id}
   PUT    /api/therapist-bundles/{id}/response
   
   # Staff Operations
   GET    /api/staff/eligible-therapists
   POST   /api/staff/manual-assignment
   GET    /api/staff/cooling-periods
   ```

2. **Update Existing Endpoints**
   - Maintain backward compatibility
   - Add deprecation headers
   - Update documentation

3. **API Versioning**
   - Implement v2 endpoints
   - Keep v1 endpoints functional
   - Plan v1 sunset date

#### Deliverables
- New API endpoints
- Updated API documentation
- Postman collection

### Phase 5: Frontend Updates (4 days)

#### Tasks
1. **Staff Tool Updates**
   - Patient search management UI
   - Bundle creation interface
   - Response recording UI
   - Cooling period visualization

2. **New Features**
   - Bulk operations support
   - Bundle preview
   - Conflict resolution UI
   - Search history view

3. **Migration of Existing Features**
   - Update placement request UI to use new models
   - Redirect old workflows to new ones
   - Add migration warnings

#### Deliverables
- Updated React components
- New staff workflows
- User documentation

### Phase 6: Testing & Validation (3 days)

#### Tasks
1. **Unit Tests**
   - Model tests
   - Algorithm tests
   - API endpoint tests

2. **Integration Tests**
   - End-to-end bundle creation
   - Cooling period enforcement
   - Parallel bundle handling

3. **Performance Tests**
   - Bundle algorithm performance
   - Database query optimization
   - API response times

4. **User Acceptance Testing**
   - Staff workflow validation
   - Edge case handling
   - Error scenario testing

#### Deliverables
- Test reports
- Performance benchmarks
- UAT sign-off

### Phase 7: Deployment & Cutover (2 days)

#### Tasks
1. **Pre-deployment**
   - Final data validation
   - Backup current state
   - Notify staff of changes

2. **Deployment**
   - Deploy database migrations
   - Deploy backend services
   - Deploy frontend updates
   - Enable feature flags

3. **Post-deployment**
   - Monitor system health
   - Track migration metrics
   - Support staff questions

4. **Cleanup**
   - Remove old API endpoints (after grace period)
   - Drop deprecated tables
   - Archive old code

#### Deliverables
- Deployment checklist
- Monitoring dashboard
- Post-deployment report

## Rollback Plan

### Database Rollback
```sql
-- Phase 1 Rollback
DROP TABLE IF EXISTS matching_service.therapeut_anfrage_patient;
DROP TABLE IF EXISTS matching_service.therapeutenanfrage;
DROP TABLE IF EXISTS matching_service.platzsuche_contact_request;
DROP TABLE IF EXISTS matching_service.platzsuche;

-- Revert column additions
ALTER TABLE patient_service.patients 
DROP COLUMN IF EXISTS max_travel_distance_km,
DROP COLUMN IF EXISTS travel_mode,
DROP COLUMN IF EXISTS availability_schedule,
DROP COLUMN IF EXISTS therapist_gender_preference,
DROP COLUMN IF EXISTS group_therapy_preference;

-- Similar for therapist table...
```

### Code Rollback
1. Disable feature flags
2. Revert to previous release
3. Clear caches
4. Notify staff

## Risk Management

### Identified Risks
1. **Algorithm Performance**: Bundle creation might be slow
   - Mitigation: Pre-calculate eligible therapists, use caching

2. **Staff Training**: New workflow complexity
   - Mitigation: Comprehensive documentation, hands-on training

3. **Data Integrity**: Parallel bundles might cause conflicts
   - Mitigation: Proper locking, conflict resolution UI

### Monitoring Plan
- API response times
- Bundle creation success rate
- Cooling period violations
- Staff productivity metrics

## Timeline Summary

| Phase | Duration | Start Date | End Date |
|-------|----------|------------|----------|
| Phase 0: Preparation | 2 days | Day 1 | Day 2 |
| Phase 1: Database | 3 days | Day 3 | Day 5 |
| Phase 2: Models | 4 days | Day 6 | Day 9 |
| Phase 3: Services | 5 days | Day 10 | Day 14 |
| Phase 4: APIs | 3 days | Day 15 | Day 17 |
| Phase 5: Frontend | 4 days | Day 18 | Day 21 |
| Phase 6: Testing | 3 days | Day 22 | Day 24 |
| Phase 7: Deployment | 2 days | Day 25 | Day 26 |

**Total Duration**: 26 working days (approximately 5-6 weeks with buffer)

## Success Criteria

1. **Technical Success**
   - All new models implemented and tested
   - APIs returning correct data
   - No data loss during migration
   - Performance within acceptable limits

2. **Business Success**
   - Staff can create bundles efficiently
   - Cooling periods properly enforced
   - Parallel bundles working correctly
   - Improved therapist response rates

3. **Operational Success**
   - Staff trained on new system
   - Documentation complete
   - Monitoring in place
   - Support processes defined

## Post-Migration Tasks

1. **Week 1-2**
   - Monitor system stability
   - Gather staff feedback
   - Fix urgent issues

2. **Week 3-4**
   - Optimize bundle algorithm
   - Enhance UI based on feedback
   - Plan old system removal

3. **Month 2**
   - Remove deprecated code
   - Analyze bundle effectiveness
   - Plan next enhancements

## Appendix: Key Decisions

1. **Keep Matching Service**: Rather than splitting into two services
2. **Feature Flags**: Enable gradual rollout and easy rollback
3. **Maintain Compatibility**: Keep old APIs during transition
4. **Manual Processes**: Rely on staff for edge cases vs full automation
5. **Parallel Implementation**: Build new alongside old, then cutover