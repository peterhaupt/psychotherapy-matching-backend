# Communication Service Migration Guide

## Overview
This guide outlines the migration of the Communication Service from a business-logic-heavy implementation to a pure infrastructure service. This is for a **DEVELOPMENT SYSTEM** - all test data will be deleted, and no backward compatibility is required.

## Migration Goals
1. Remove all business logic from Communication Service
2. Move template management to requesting services
3. Move scheduling algorithms to Matching/Therapist services  
4. Implement Markdown support and legal footer injection
5. Simplify to pure send/track functionality
6. Remove all email templates from the service

## Migration Status
- ✅ **Phase 1: Database Migration** - COMPLETED
- ✅ **Phase 2.1: Update Models** - COMPLETED
- ✅ **Phase 2.2: Add Dependencies** - COMPLETED
- ✅ **Phase 2.3: Create New Utilities** - COMPLETED
- ✅ **Phase 2.5: Update Email API** - COMPLETED
- ✅ **Phase 2.6: Remove Business Logic** - COMPLETED
- ✅ **Phase 2.7: Update Configuration** - COMPLETED
- 🔄 **Phase 3: Update Other Services** - PENDING
- 🔄 **Phase 4: Testing** - PENDING
- 🔄 **Phase 5: Cleanup** - PENDING

## Pre-Migration Checklist
- ✅ Stop all services: `docker-compose down`
- ✅ Ensure you have latest code from all repositories
- ✅ Have the updated `001_initial_setup.py` file ready (Phase 1 changes already included)

---

## Phase 1: Database Migration ✅ COMPLETED

The database migration script has been updated to include all Phase 1 changes:

### Changes Applied in Migration Script:
1. **Email table**: Removed `nachverfolgung_erforderlich` and `nachverfolgung_notizen` columns
2. **Phone call table**: Removed `wiederholen_nach` column

### To Apply the Migration:
```bash
# Stop all services
docker-compose down

# Remove the database volume completely
docker-compose down -v

# Start only the database services
docker-compose up -d postgres pgbouncer

# Wait for postgres to be ready (about 10 seconds)
sleep 10

# Run the updated migration (with Phase 1 changes already included)
cd migrations
alembic upgrade head

# Verify the migration
docker-compose exec postgres psql -U $DB_USER -d therapy_platform -c "\dt *.*"
```

---

## Phase 2: Update Communication Service Code

### Step 2.1: Update Models ✅ COMPLETED

The following model updates have been completed:

**Email Model (`communication_service/models/email.py`)**:
- ✅ Removed `nachverfolgung_erforderlich` field
- ✅ Removed `nachverfolgung_notizen` field

**Phone Call Model (`communication_service/models/phone_call.py`)**:
- ✅ Removed `wiederholen_nach` field
- ✅ Updated `mark_as_failed` method to remove `retry_date` parameter

### Step 2.2: Add Dependencies ✅ COMPLETED

**File: `communication_service/requirements.txt`**

The requirements.txt file has been updated to include new dependencies for markdown and HTML processing:
- Added markdown-it-py==3.0.0
- Added beautifulsoup4==4.12.3

### Step 2.3: Create New Utilities ✅ COMPLETED

**New File: `communication_service/utils/markdown_processor.py`**

Created markdown processor utility with the following functions:
- `markdown_to_html()`: Converts markdown to HTML
- `strip_html()`: Strips HTML tags to create plain text
- `wrap_with_styling()`: Wraps HTML content with styling and optional footer
- `get_legal_footer()`: Returns the legal footer HTML

### Step 2.5: Update Email API ✅ COMPLETED

**File: `communication_service/api/emails.py`**

Updated the POST endpoint to accept markdown:
- Added `body_markdown` parameter
- Added `add_legal_footer` parameter (default: True)
- Added logic to convert markdown to HTML when `body_markdown` is provided
- Integrated with the new markdown processor utilities

### Step 2.6: Remove Business Logic ✅ COMPLETED

**File: `communication_service/utils/email_sender.py`**
- ✅ Removed: `can_contact_therapist()` function
- ✅ Removed: `MIN_DAYS_BETWEEN_EMAILS` constant
- ✅ Removed: Any frequency checking logic

**File: `communication_service/utils/phone_call_scheduler.py`**
- ✅ Removed: All complex scheduling algorithm functions
- ✅ Simplified: `find_available_slot()` to return basic default slots
- ✅ Kept only: Basic database operations

**File: `communication_service/events/consumers.py`**
- ✅ Removed: `check_unanswered_emails_worker()` function
- ✅ Removed: Automated follow-up logic
- ✅ Kept only: Basic event handling for send requests

### Step 2.7: Update Configuration ✅ COMPLETED

**File: `shared/config/settings.py`**
- ✅ Added new configuration option: `EMAIL_ADD_LEGAL_FOOTER`
- ✅ Updated company references to "Curavani Therapievermittlung GmbH"
- ✅ Updated default email sender to use curavani.de domain
- ✅ Added `COMPANY_NAME` and `COMPANY_DOMAIN` configuration

---

## Phase 3: Update Other Services 🔄 PENDING

### Step 3.1: Move Templates to Matching Service
All email templates will be removed from the communication service. The matching service will be responsible for generating email content as markdown.

### Step 3.2: Update Matching Service Bundle Creation
**File: `matching_service/services.py`**

Update `CommunicationService.create_bundle_email()` to:
1. Generate markdown content instead of HTML
2. Remove template references
3. Use new markdown field in API call

### Step 3.3: Update Patient Service Communication
**File: `patient_service/utils/communication.py`**

Update all email functions to:
1. Generate markdown content
2. Use `body_markdown` field instead of `body_html`
3. Remove template parameters

---

## Phase 4: Testing 🔄 PENDING

### Step 4.1: Start All Services
```bash
# Rebuild all images with new dependencies
docker-compose build

# Start all services
docker-compose up -d

# Check logs for errors
docker-compose logs -f
```

### Step 4.2: Test Email Creation
```bash
# Test markdown email
curl -X POST http://localhost:8004/api/emails \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": 1,
    "betreff": "Test Markdown Email",
    "body_markdown": "# Hello\n\nThis is a **test** email with:\n\n- Bullet points\n- *Italic text*\n- [Links](https://example.com)",
    "empfaenger_email": "test@example.com",
    "empfaenger_name": "Test User"
  }'
```

### Step 4.3: Test Phone Call Creation
```bash
# Test simple phone call (no auto-scheduling)
curl -X POST http://localhost:8004/api/phone-calls \
  -H "Content-Type: application/json" \
  -d '{
    "therapist_id": 1,
    "geplantes_datum": "2025-06-20",
    "geplante_zeit": "14:00",
    "notizen": "Follow-up call"
  }'
```

---

## Phase 5: Cleanup 🔄 PENDING

### Step 5.1: Remove Unused Files
```bash
# Remove template directory from communication service
rm -rf communication_service/templates/

# Remove unused utility functions
# (Manual review of utils/ directory recommended)
```

### Step 5.2: Update Documentation
- Update API_REFERENCE.md to reflect removed fields
- Update service documentation to reflect new responsibilities
- Add examples of markdown usage

---

## Rollback Plan

If issues arise:
1. Stop all services: `docker-compose down`
2. Use original `001_initial_setup.py` (without Phase 1 changes)
3. Delete database volume: `docker-compose down -v`
4. Restore original code from git
5. Rebuild and restart

---

## Success Criteria

- ✅ Database migration applied successfully (Phase 1 changes included)
- ✅ Model files updated to remove deprecated fields (Phase 2.1 completed)
- ✅ Dependencies updated for markdown support (Phase 2.2 completed)
- ✅ Markdown processor utility created (Phase 2.3 completed)
- ✅ Email API updated to support markdown (Phase 2.5 completed)
- ✅ Business logic removed from Communication service (Phase 2.6 completed)
- ✅ Configuration updated for Curavani branding (Phase 2.7 completed)
- [ ] Communication service starts without errors
- [ ] Emails can be created with markdown content
- [ ] Legal footer appears in emails when enabled
- [ ] Phone calls can be created with specific date/time
- [ ] No automated follow-up calls are created
- [ ] No frequency limiting on emails
- [ ] Other services can create communications successfully
- [ ] All email templates removed from the service

---

## Notes

- Phase 1 database changes are already included in the migration script
- Phase 2 (steps 2.1 through 2.7) are now completed
- No backward compatibility needed - this is a development system
- All test data will be deleted during migration
- Email templates will be completely removed from the communication service
- Business logic has been simplified to basic infrastructure operations only
- Complex scheduling algorithms should now be implemented in requesting services
