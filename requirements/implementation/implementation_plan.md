# Implementation Plan - Current Status

## Phase 3: Bundle-Based Matching System 🚧 IN PROGRESS

### Overview
Transform the current basic matching system into the bundle-based system described in business requirements. Database schema is complete with German field names - now updating code to match.

### Week 1-2: Database Schema Updates ✅ COMPLETED

**What Was Accomplished:**
- ✅ Created all bundle system tables with German names
- ✅ Renamed ALL database fields to German
- ✅ Removed placement_requests table completely
- ✅ Removed communication batch tables
- ✅ Updated all foreign key relationships
- ✅ All database migrations applied successfully
- ✅ Database tests passing (test_database_schemas.py)

### Week 3: Model & Code Updates 🔄 CURRENT WEEK

## 🚨 CRITICAL ISSUES BLOCKING PROGRESS

### Issue 1: Matching Service Crashes 🔴
**Problem**: Any request to `/api/placement-requests/*` causes 500 error
**Root Cause**: `placement_requests` table removed from database but code still tries to query it
**Impact**: Entire matching service is unusable
**Priority**: MUST FIX FIRST

### Issue 2: Model/Database Mismatches ⚠️
**Problem**: Models use English field names, database uses German
**Affected Services**: Therapist, Communication
**Impact**: Create/Update operations fail with "column does not exist" errors
**Priority**: Fix after matching service

## Emergency Fix Plan (Today)

### Step 1: Stop the Crashes (1-2 hours)
```python
# In matching_service/api/matching.py
# Replace all endpoints with:

class PlacementRequestResource(Resource):
    def get(self, request_id):
        return {'message': 'Bundle system not yet implemented'}, 501
    
    def put(self, request_id):
        return {'message': 'Bundle system not yet implemented'}, 501
    
    def delete(self, request_id):
        return {'message': 'Bundle system not yet implemented'}, 501

class PlacementRequestListResource(Resource):
    def get(self):
        return {'message': 'Bundle system not yet implemented'}, 501
    
    def post(self):
        return {'message': 'Bundle system not yet implemented'}, 501
```

### Step 2: Remove PlacementRequest Model (30 minutes)
1. Delete `matching_service/models/placement_request.py`
2. Update `matching_service/models/__init__.py` (remove import)
3. Update `migrations/alembic/env.py` (remove import)
4. Search entire codebase for "PlacementRequest" and remove

### Step 3: Create Stub Bundle Models (1 hour)
Create minimal models just to stop import errors:

```python
# matching_service/models/platzsuche.py
class Platzsuche(Base):
    __tablename__ = "platzsuche"
    __table_args__ = {"schema": "matching_service"}
    # Add basic fields to match database
```

## Revised Implementation Schedule

### Day 1 (Today) - Emergency Fixes 🚨

**Morning: Stop the Bleeding**
- [ ] Fix matching service crashes (2 hours)
- [ ] Remove PlacementRequest completely (30 min)
- [ ] Create stub bundle models (1 hour)
- [ ] Verify no more 500 errors (30 min)

**Afternoon: Update Therapist Model**
- [ ] Open `therapist_service/models/therapist.py`
- [ ] Rename fields to German (match database)
- [ ] Update API response marshalling
- [ ] Test all endpoints

### Day 2 - Communication Service Updates

**Morning: Update Models**
- [ ] Update Email model fields to German
- [ ] Update PhoneCall model fields to German
- [ ] Remove EmailBatch model
- [ ] Remove PhoneCallBatch model

**Afternoon: Fix APIs**
- [ ] Update email API field names
- [ ] Update phone call API field names
- [ ] Remove batch endpoints
- [ ] Test with Matching Service

### Day 3 - Bundle Models Implementation

**Morning: Complete Models**
- [ ] Implement Platzsuche model fully
- [ ] Implement Therapeutenanfrage model
- [ ] Implement TherapeutAnfragePatient model
- [ ] Add model relationships and methods

**Afternoon: Start Bundle Algorithm**
- [ ] Create bundle_creator.py
- [ ] Implement hard constraints
- [ ] Add distance checking
- [ ] Add exclusion checking

### Day 4 - Bundle Algorithm Completion

**Morning: Progressive Filtering**
- [ ] Implement availability matching
- [ ] Add preference scoring
- [ ] Sort by wait time
- [ ] Bundle size optimization

**Afternoon: API Endpoints**
- [ ] Create /api/platzsuchen endpoints
- [ ] Create /api/therapeutenanfragen endpoints
- [ ] Add bundle creation endpoint
- [ ] Response recording endpoint

### Day 5 - Integration & Testing

**Morning: Service Integration**
- [ ] Connect bundle creation to email sending
- [ ] Implement cooling period updates
- [ ] Add conflict resolution
- [ ] Event publishing

**Afternoon: Testing**
- [ ] Unit tests for algorithm
- [ ] API endpoint tests
- [ ] Integration test full flow
- [ ] Performance testing

## Updated Task Checklist

### Immediate Actions (Block Everything Else)
- [ ] Fix matching service 500 errors
- [ ] Remove all PlacementRequest code
- [ ] Create minimal bundle models
- [ ] Verify services don't crash

### Model Updates (Day 1-2)
- [ ] Therapist model → German fields
- [ ] Email model → German fields  
- [ ] PhoneCall model → German fields
- [ ] Remove batch models
- [ ] Update all model imports

### Bundle Implementation (Day 3-4)
- [ ] Complete bundle models
- [ ] Bundle creation algorithm
- [ ] Progressive filtering
- [ ] API endpoints

### Integration (Day 5)
- [ ] Service connections
- [ ] Event handling
- [ ] Full flow testing
- [ ] Documentation

## Testing Strategy

### After Each Model Update
```bash
# Test model can be imported
docker-compose exec [service_name] python -c "from models import *"

# Test API endpoints
curl http://localhost:[port]/api/[endpoint]

# Check logs for errors
docker-compose logs [service_name]
```

### Integration Testing
```bash
# Test full bundle creation flow
python tests/integration/test_bundle_creation.py

# Monitor events
python tests/integration/all_topics_monitor.py
```

## Success Criteria

### Phase Complete When:
1. ✅ No 500 errors on any endpoint
2. ✅ All models use German field names matching database
3. ✅ Bundle system creates groups of 3-6 patients
4. ✅ Cooling periods enforced (4 weeks)
5. ✅ Progressive filtering works correctly
6. ✅ Can handle 100+ active patient searches
7. ✅ Integration tests pass

## Risk Mitigation

### Current Risks
1. **Service Downtime**: Matching service currently broken
   - Mitigation: Emergency fix today
   
2. **Data Loss**: Models don't match database
   - Mitigation: Careful field mapping, extensive testing
   
3. **Integration Issues**: Services may not work together
   - Mitigation: Test after each change
   
4. **Performance**: Bundle algorithm may be slow
   - Mitigation: Start simple, optimize later

### Rollback Plan
- Database migrations are reversible (but don't rollback)
- Keep old model files until new ones work
- Git commit after each successful change
- Can disable bundle system via feature flag

## Communication Plan

### For Frontend Team
- Matching Service will return 501 (Not Implemented) instead of 500 errors
- Field names changing to German - will provide mapping
- New endpoints coming Day 4
- Full API documentation update on Day 5

### For Testing Team  
- System partially broken right now
- Emergency fixes in progress
- Will provide test plan by Day 3
- Need test data with German field names

### For Stakeholders
- Database migration complete ✅
- Code updates in progress (5 days)
- Bundle system operational by end of week
- No data loss, just code updates needed

---
*Current Status: Database ready, fixing code to match*
*Critical Issue: Matching service crashes - fixing NOW*
*ETA for Stability: End of Day 1*
*ETA for Bundle System: End of Week*