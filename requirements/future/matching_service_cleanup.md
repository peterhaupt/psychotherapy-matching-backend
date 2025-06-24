# Matching Service - Legacy Cleanup & Future Changes

**Document Version:** 1.0  
**Date:** December 2024  
**Status:** Planning Phase

## Overview

This document outlines legacy functionality that needs to be removed from the Matching Service and future changes required to modernize the codebase. The current system has evolved from an automated matching approach to a manual therapist selection workflow, leaving several orphaned features.

---

## 🗑️ Legacy Functionality to Remove

### 1. Contact Request System (High Priority)

**Problem:** The contact request system (`kontaktanfrage`) was designed for automated matching but serves no purpose in the current manual workflow.

#### Components to Remove:

**API Endpoint:**
- `POST /api/platzsuchen/{id}/kontaktanfrage` 
- File: `api/anfrage.py` - `KontaktanfrageResource` class
- Route registration in `app.py`

**Database Field:**
- `Platzsuche.gesamt_angeforderte_kontakte` field
- Database migration to drop column

**Model Methods:**
- `Platzsuche.update_contact_count()`
- References in `__init__.py` and API responses

**API Response Fields:**
- Remove `gesamt_angeforderte_kontakte` from:
  - `GET /api/platzsuchen` responses
  - `GET /api/platzsuchen/{id}` responses

#### Impact Assessment:
- ✅ **Safe to remove** - No current functionality depends on this
- ✅ **No breaking changes** - Manual workflow doesn't use these features
- ⚠️ **Database migration required**

---

### 2. Bundle System References (Medium Priority)

**Problem:** Code comments and variable names still reference the old "bundle" terminology instead of "anfrage" (inquiry).

#### Files to Clean Up:

**Comments and Documentation:**
- `algorithms/anfrage_creator.py` - Update comments mentioning "bundle"
- `models/therapeut_anfrage_patient.py` - Field comment "renamed from bundle"
- `api/__init__.py` - Comments about "Bundle/Bündel" terminology

**Database Constraints:**
- Review constraint names for consistency:
  - `anfrage_size_check` constraint (uses German "anfrage" ✓)
  - `uq_therapeut_anfrage_patient_anfrage_search` (consistent ✓)

---

### 3. Minimum Inquiry Size Validation (Low Priority)

**Problem:** Database constraint and validation still enforce minimum 3 patients, but API documentation states minimum is 1.

#### Current State:
```sql
CheckConstraint('anfragegroesse >= 3 AND anfragegroesse <= 6', name='anfrage_size_check')
```

#### Decisions Needed:
- **Option A:** Update constraint to `>= 1` to match API docs
- **Option B:** Update API docs to reflect `>= 3` minimum
- **Option C:** Make configurable via `anfrage_config`

---

### 4. Cross-Service Foreign Key References (Cleanup)

**Problem:** Some models still have commented-out or inconsistent foreign key references.

#### Files to Review:
- `models/platzsuche.py` - Patient relationship comments
- `models/therapeut_anfrage_patient.py` - Cross-service field documentation
- `models/therapeutenanfrage.py` - Communication service references

---

## 🔧 Database Schema Changes Required

### Migration 1: Remove Contact Request Fields
```sql
-- Remove legacy contact request field
ALTER TABLE matching_service.platzsuche 
DROP COLUMN IF EXISTS gesamt_angeforderte_kontakte;
```

### Migration 2: Update Inquiry Size Constraints (If Decided)
```sql
-- Option A: Allow single-patient inquiries
ALTER TABLE matching_service.therapeutenanfrage 
DROP CONSTRAINT IF EXISTS anfrage_size_check;

ALTER TABLE matching_service.therapeutenanfrage 
ADD CONSTRAINT anfrage_size_check 
CHECK (anfragegroesse >= 1 AND anfragegroesse <= 6);
```

---

## 🚀 Future Enhancements & Improvements

### 1. Configuration Improvements (Medium Priority)

**Current Issue:** Hard-coded values scattered throughout codebase.

#### Centralize Configuration:
```python
# shared/config.py additions needed
ANFRAGE_CONFIG = {
    'min_size': 1,  # Make configurable
    'max_size': 6,
    'plz_match_digits': 2,
    'default_max_distance_km': 25,
    'cooling_period_weeks': 4  # Currently hard-coded
}
```

#### Files to Update:
- `algorithms/anfrage_creator.py` - Use config for all constants
- `models/therapeutenanfrage.py` - Dynamic constraint validation
- `services.py` - Use config for cooling periods

---

### 2. Error Handling Improvements (High Priority)

**Current Issue:** Inconsistent error handling across API endpoints.

#### Standardize Error Responses:
- Create common error response format
- Add specific error codes for different failure scenarios
- Improve validation error messages (currently mix English/German)

#### Files to Improve:
- `api/anfrage.py` - All resource classes
- `services.py` - Cross-service communication errors
- `algorithms/anfrage_creator.py` - Constraint validation errors

---

### 3. API Documentation Updates (High Priority)

**Current Issue:** API docs don't fully reflect current implementation.

#### Updates Needed:
- Remove `kontaktanfrage` endpoint documentation
- Remove `gesamt_angeforderte_kontakte` field from examples
- Clarify minimum inquiry size (1 vs 3)
- Add more detailed error response examples
- Document PLZ prefix validation rules

---

### 4. Testing Infrastructure (High Priority)

**Current Issue:** Test files are mostly stubs.

#### Test Coverage Needed:
- `tests/test_matching.py` - Currently just placeholder
- Unit tests for algorithm functions
- Integration tests for API endpoints
- Mock tests for cross-service communication

#### Test Scenarios:
- Therapist selection with various PLZ prefixes
- Constraint validation (distance, preferences, exclusions)
- Inquiry creation and response handling
- Error conditions and edge cases

---

### 5. Monitoring & Observability (Medium Priority)

**Current Issue:** Limited operational visibility.

#### Add Metrics:
- Inquiry creation rates
- Therapist response rates
- Patient placement success rates
- Cross-service communication failures

#### Add Health Checks:
- Database connectivity
- Cross-service API availability
- Kafka consumer status

---

### 6. Performance Optimizations (Low Priority)

**Current Issue:** N+1 query patterns in some endpoints.

#### Optimization Opportunities:
- `GET /platzsuchen` - Batch patient data fetching
- `GET /therapeutenanfragen` - Batch therapist data fetching
- Database query optimization for large datasets
- Caching for frequently accessed therapist data

---

## 📋 Implementation Priority Matrix

| Priority | Component | Effort | Risk | Business Impact |
|----------|-----------|--------|------|-----------------|
| **High** | Remove Contact Request System | Medium | Low | Medium (Code clarity) |
| **High** | API Documentation Updates | Low | Low | High (User confusion) |
| **High** | Error Handling Standardization | Medium | Low | High (User experience) |
| **High** | Testing Infrastructure | High | Low | High (Quality assurance) |
| **Medium** | Configuration Centralization | Medium | Medium | Medium (Maintainability) |
| **Medium** | Bundle References Cleanup | Low | Low | Low (Code clarity) |
| **Medium** | Monitoring & Observability | Medium | Low | Medium (Operations) |
| **Low** | Inquiry Size Validation | Low | Medium | Low (Business rule clarity) |
| **Low** | Performance Optimizations | High | Medium | Low (Current scale) |

---

## 🚨 Breaking Changes Impact Assessment

### API Changes:
- **Removing `kontaktanfrage` endpoint:** ❌ **Breaking Change**
  - Impact: Any client using this endpoint will fail
  - Mitigation: Verify no active usage before removal

- **Removing `gesamt_angeforderte_kontakte` field:** ❌ **Breaking Change**
  - Impact: Client parsing API responses may fail
  - Mitigation: Version API or provide deprecation period

### Database Changes:
- **Column removal:** ⚠️ **Requires Migration**
  - Impact: Existing data in `gesamt_angeforderte_kontakte` will be lost
  - Mitigation: Data appears to be display-only, safe to remove

### Service Dependencies:
- **No external service dependencies** for legacy removal ✅
- **Cross-service calls remain unchanged** ✅

---

## 📝 Implementation Steps

### Phase 1: Preparation (Week 1)
1. ✅ Document all legacy components (this document)
2. 🔄 Verify no active usage of `kontaktanfrage` endpoint
3. 🔄 Review client applications for `gesamt_angeforderte_kontakte` usage
4. 🔄 Create database backup strategy

### Phase 2: Code Cleanup (Week 2)
1. 🔄 Remove `KontaktanfrageResource` class and route
2. 🔄 Remove `gesamt_angeforderte_kontakte` field and methods
3. 🔄 Update API response models
4. 🔄 Clean up bundle terminology references
5. 🔄 Update API documentation

### Phase 3: Database Migration (Week 3)
1. 🔄 Create and test database migration
2. 🔄 Deploy migration to staging environment
3. 🔄 Validate all functionality still works
4. 🔄 Deploy to production

### Phase 4: Future Enhancements (Ongoing)
1. 🔄 Implement standardized error handling
2. 🔄 Add comprehensive test coverage
3. 🔄 Centralize configuration
4. 🔄 Add monitoring and metrics

---

## ⚠️ Risk Mitigation

### Rollback Plan:
- **Database migration rollback script** ready
- **Git branch protection** for easy revert
- **Feature flag** for new error handling (if needed)

### Testing Strategy:
- **Manual testing** of all API endpoints post-cleanup
- **Integration testing** with other services
- **Load testing** to ensure no performance regression

### Communication Plan:
- **Notify API users** of upcoming breaking changes
- **Update API documentation** before deployment
- **Provide migration guide** for affected clients

---

## 📞 Contact & Review

**Document Owner:** Development Team  
**Last Review:** December 2024  
**Next Review:** After Phase 1 completion

**Approval Required From:**
- [ ] Technical Lead
- [ ] Product Owner  
- [ ] Operations Team

---

*This document should be updated as implementation progresses and new requirements are discovered.*