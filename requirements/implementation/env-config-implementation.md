# Multi-Environment Configuration Implementation Guide

## Overview

This document provides a step-by-step implementation guide for refactoring the Curavani backend to support three distinct environments (Development, Test, Production) with fully configurable environment variables and no hardcoded values.

### Goals
1. ✅ Fix critical data loss bug in patient-service GCS import
2. Remove all hardcoded configuration values
3. Create three distinct environments with proper isolation
4. Enable tests to run against any environment
5. Add configuration validation at startup

### Environment Structure

| Environment | API Ports | Database Name | Docker Suffix |
|------------|-----------|---------------|---------------|
| Development | 8001-8005 | therapy_platform | (none) |
| Test | 8011-8015 | curavani_test | -test |
| Production | 8021-8025 | curavani_prod | -prod |

---

## ✅ Phase 0: Critical Bug Fix (COMPLETED)

### Issue: Patient GCS Import Data Loss

**Current Problem**: Files are deleted from GCS even if database write fails, causing permanent data loss.

### ✅ Step 0.1: Analyze Current Implementation

**Status: COMPLETED** - Analysis revealed that the existing implementation already had a backup mechanism in place:

- Files that fail import are automatically moved to a local `failed/` folder
- GCS files are only deleted after successful processing
- Error notifications are sent for failed imports
- Import status tracking is maintained

### ✅ Step 0.2: Implement Safe Import Pattern

**Status: COMPLETED** - The safe import pattern was already implemented:

```
1. Download file to temp location
2. Parse and validate JSON
3. Begin database transaction
4. Import patient
5. Commit transaction
6. Only if commit successful: Delete from GCS
7. If any failure: Keep file in GCS, move local copy to failed/, log error
```

### ✅ Step 0.3: Add Import Recovery

**Status: COMPLETED** - Added comprehensive unit tests to verify the backup mechanism works in all failure scenarios:
- Database connection failures
- JSON parsing errors
- Validation failures
- Transaction rollbacks
- Import status endpoint for monitoring
- Manual retry capability through re-uploading to GCS

---

## ✅ Phase 1: Audit Current State (COMPLETED)

### ✅ Step 1.1: Service Audit Checklist

**Status: COMPLETED** - Comprehensive audit performed across all services for hardcoded values.

### ✅ Step 1.2: Document All Environment Variables

**Status: COMPLETED** - Complete audit results by priority:

#### 🔴 **CRITICAL Priority - Import System Issues**

**Patient Service** (`imports/gcs_monitor.py`):
- Default bucket: `'dev-patient-import'`
- Default local path: `'/data/patient_imports/development'`
- Default check interval: `300` seconds

**Therapist Service** (`imports/file_monitor.py`):
- Default base path: `'../../curavani_scraping/data/processed'`
- Default check interval: `86400` seconds (24 hours)

#### 🟡 **HIGH Priority - Algorithm & Business Logic**

**Matching Service** (`services.py`):
- Default fallback times: `"10:00"`, `"14:00"`
- Default durations: `5` minutes, `10` minutes
- Tomorrow calculation: `timedelta(days=1)`

**Communication Service** (`utils/email_sender.py`):
- Batch limit: `limit=10`
- Timeout values: `timeout=5`, `timeout=10`

#### 🟠 **MEDIUM Priority - External API Configuration**

**Geocoding Service** (`utils/osm.py`):
- Request timeouts: various `timeout=10` values
- Retry delays: `time.sleep(2 ** attempt)`
- Rate limiting intervals: `time.sleep(1)`
- Coordinate precision: `round(*, 6)`

#### 🟢 **LOW Priority - Infrastructure**

**All Services**:
- Host binding: `host="0.0.0.0"` in all `app.py` files
- Database defaults: Various `default=False`, `default=date.today()` in models
- Date handling: `date.today()` calls throughout API endpoints

**Priority Assessment:**
1. **🔴 CRITICAL**: Import system paths and intervals (data loss risk)
2. **🟡 HIGH**: Algorithm parameters affecting business logic  
3. **🟠 MEDIUM**: External API timeouts and retry logic
4. **🟢 LOW**: Infrastructure defaults and database field defaults

---

## Phase 2: Environment Structure Design

### Step 2.1: Create Master Environment Structure

```ini
# ===================================
# GENERAL CONFIGURATION
# ===================================

# Environment Settings
FLASK_ENV=                  # development|test|production
SERVICE_ENV_SUFFIX=         # ""|-test|-prod

# Database Configuration
DB_USER=
DB_PASSWORD=
DB_NAME=                    # therapy_platform|curavani_test|curavani_prod
DB_HOST=postgres${SERVICE_ENV_SUFFIX}
DB_PORT=5432

# PgBouncer Configuration  
PGBOUNCER_HOST=pgbouncer${SERVICE_ENV_SUFFIX}
PGBOUNCER_PORT=6432

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=kafka${SERVICE_ENV_SUFFIX}:9093
KAFKA_ZOOKEEPER_CONNECT=zookeeper${SERVICE_ENV_SUFFIX}:2181

# ===================================
# SERVICE PORTS
# ===================================

# Development: 8001-8005, Test: 8011-8015, Production: 8021-8025
PATIENT_SERVICE_PORT=
THERAPIST_SERVICE_PORT=
MATCHING_SERVICE_PORT=
COMMUNICATION_SERVICE_PORT=
GEOCODING_SERVICE_PORT=

# ===================================
# PATIENT SERVICE CONFIGURATION
# ===================================

# GCS Import Settings
GCS_IMPORT_BUCKET=          # dev-patient-import|test-patient-import|curavani-production-data
GCS_READER_CREDENTIALS_PATH=/credentials/gcs-reader${SERVICE_ENV_SUFFIX}.json
GCS_DELETER_CREDENTIALS_PATH=/credentials/gcs-deleter${SERVICE_ENV_SUFFIX}.json
PATIENT_IMPORT_LOCAL_PATH=/data/patient_imports/${FLASK_ENV}
PATIENT_IMPORT_CHECK_INTERVAL_SECONDS=300

# ===================================
# THERAPIST SERVICE CONFIGURATION
# ===================================

THERAPIST_IMPORT_FOLDER_PATH=/scraping_data
THERAPIST_IMPORT_CHECK_INTERVAL_SECONDS=86400
THERAPIST_IMPORT_ENABLED=true

# ===================================
# MATCHING SERVICE CONFIGURATION
# ===================================

MAX_ANFRAGE_SIZE=6
MIN_ANFRAGE_SIZE=1
PLZ_MATCH_DIGITS=2
FOLLOW_UP_THRESHOLD_DAYS=7
DEFAULT_PHONE_CALL_TIME=12:00

# ===================================
# COMMUNICATION SERVICE CONFIGURATION
# ===================================

SMTP_HOST=
SMTP_PORT=
SMTP_USERNAME=
SMTP_PASSWORD=
EMAIL_SENDER=
EMAIL_SENDER_NAME=
SYSTEM_NOTIFICATION_EMAIL=

# ===================================
# GEOCODING SERVICE CONFIGURATION
# ===================================

OSM_API_URL=https://nominatim.openstreetmap.org
OSRM_API_URL=https://router.project-osrm.org
CACHE_TTL_SECONDS=2592000
```

### Step 2.2: Create Environment-Specific Files

Create three files:
- `.env.dev`
- `.env.test`
- `.env.prod`

---

## Phase 3: Code Implementation

### Step 3.1: Update settings.py

Transform `shared/config/settings.py` to minimal version:

**Key Changes**:
1. Remove ALL default values
2. Add validation method
3. Keep only type conversion and computed properties
4. Add required field validation

### Step 3.2: Fix Service-Specific Hardcoded Values

#### Patient Service Fixes

**File: `imports/gcs_monitor.py`**
- Remove default bucket name
- Remove default paths
- Make all config required

**File: `models/patient.py`**
- Move database defaults to configuration (optional)
- Or document as application-level defaults

**File: `api/patients.py` & `events/consumers.py`**
- Consider timezone configuration for date handling

#### Similar fixes for all other services...

### Step 3.3: Add Startup Validation

Each service's `app.py` should:
1. Validate all required environment variables
2. Log configuration (non-sensitive)
3. Fail fast with clear error messages

---

## Phase 4: Test Framework Updates

### Step 4.1: Create conftest.py

Location: `tests/conftest.py`

**Features**:
- Load environment files based on --env parameter
- Provide service URL fixtures
- Handle test isolation

### Step 4.2: Update Test Files

All test files need updates:
- Remove hardcoded URLs
- Use fixtures for service endpoints
- Add environment-aware setup

### Step 4.3: Test Isolation Strategy

- Unique test prefixes per environment
- Cleanup procedures
- Data isolation verification

---

## Phase 5: Infrastructure Setup

### Step 5.1: Create docker-compose.test.yml

New file with:
- Test-specific service names (suffix: -test)
- Test ports (8011-8015)
- Test database
- Isolated networks

### Step 5.2: Update docker-compose.prod.yml

Change production ports from 8011-8015 to 8021-8025

### Step 5.3: Makefile Updates

New commands:
```makefile
# Test environment commands
test-up:
test-down:
test-logs:
test-db:

# Run tests against different environments
test-against-dev:
test-against-test:
test-against-prod:

# Environment validation
validate-env-dev:
validate-env-test:
validate-env-prod:
```

---

## Phase 6: Documentation Updates

### Step 6.1: Update README.md

Add sections for:
- Three-environment architecture
- Environment setup guide
- Configuration reference
- Testing guide

### Step 6.2: Update API_REFERENCE.md

Update all port references:
- Development: 8001-8005
- Test: 8011-8015
- Production: 8021-8025

### Step 6.3: Create CONFIGURATION.md

New file documenting:
- All environment variables
- Required vs optional
- Validation rules
- Common issues

---

## Implementation Schedule

### Week 1: Critical Fix & Audit
- Day 1-2: ✅ Fix GCS import bug (Phase 0)
- Day 3-4: ✅ Complete service audit (Phase 1)
- Day 5: Design environment structure (Phase 2)

### Week 2: Core Implementation
- Day 1-2: Update settings.py and services (Phase 3)
- Day 3-4: Update test framework (Phase 4)
- Day 5: Create test infrastructure (Phase 5)

### Week 3: Documentation & Testing
- Day 1-2: Update documentation (Phase 6)
- Day 3-5: Integration testing & fixes

---

## Verification Checklist

### After Each Phase:

- [ ] All services start successfully
- [ ] No hardcoded values remain
- [ ] Tests pass in all environments
- [ ] Configuration is validated at startup
- [ ] Documentation is updated

### Final Verification:

- [ ] Development environment works (ports 8001-8005)
- [ ] Test environment works (ports 8011-8015)
- [ ] Production environment works (ports 8021-8025)
- [ ] Tests can run against any environment
- [ ] No data loss in GCS import
- [ ] All configuration is external

---

## Rollback Plan

### Before Starting:
1. Full backup of current configuration
2. Git branch for all changes
3. Document current working state

### If Issues Arise:
1. Revert to backed up .env files
2. Revert code changes via git
3. Restore original docker-compose files
4. Restart all services

### Emergency Contacts:
- Document who to contact for various issues
- Keep rollback scripts ready

---

## Appendix A: Configuration Reference

### Required Environment Variables by Service

#### All Services:
- DB_USER, DB_PASSWORD, DB_NAME
- PGBOUNCER_HOST, PGBOUNCER_PORT
- KAFKA_BOOTSTRAP_SERVERS
- FLASK_ENV

#### Service-Specific:
[Detailed list of required variables per service]

---

## Appendix B: Common Issues

### Issue: Service won't start
- Check all required environment variables
- Verify database connectivity
- Check port availability

### Issue: Tests fail in specific environment
- Verify correct .env file loaded
- Check service accessibility
- Verify test data isolation

---

## Appendix C: Migration Scripts

### Script: Validate Environment
```bash
#!/bin/bash
# validate-env.sh
# Checks all required environment variables are set
```

### Script: Migrate Configuration
```bash
#!/bin/bash  
# migrate-config.sh
# Helps migrate from old to new configuration
```

---

## Notes

- Always test changes in development first
- Keep .env files secure and out of version control
- Document any deviations from this plan
- Communicate breaking changes to team

---

*Last Updated: [Date]*
*Version: 1.1*
*Status: Phase 0 ✅ COMPLETED, Phase 1 ✅ COMPLETED*