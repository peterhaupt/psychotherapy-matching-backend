# Complete Implementation Plan - UPDATED
## Email Templates, PDF Attachments, and Matching Service Cleanup

**Version**: 4.0  
**Date**: January 2025  
**Scope**: Backend implementation for five features  
**Last Updated**: January 29, 2025 - Features 1, 2, and 3 (except old template deletion) completed

---

## Overview

This document provides a complete implementation plan for:
1. ✅ **COMPLETED** - Fixing email formatting issues when therapist has no title
2. ✅ **COMPLETED** - Removing legacy code from matching service
3. ✅ **COMPLETED** - Implementing enhanced patient success email system with 4 templates
4. **PENDING** - Adding PDF attachment functionality for therapist forms
5. **PENDING** - API documentation and frontend updates for breaking changes
6. **PENDING** - Delete old patient_success.md template (moved to end for safe deployment)

---

## Feature 1: Fix Email Formatting Error ✅ COMPLETED

### Implementation (COMPLETED - January 29, 2025)
- Fixed `patient_success.md` template with conditional checks in 4 places
- Verified other templates were already fixed
- Removed fallback function `create_default_patient_success_message()` from `anfrage.py`
- System now properly fails if template is missing instead of using fallback

### Files Modified
```
shared/templates/emails/
└── patient_success.md (4 fixes applied)

matching_service/api/
└── anfrage.py (removed fallback function)
```

---

## Feature 2: Matching Service Legacy Code Removal ✅ COMPLETED

### Implementation (COMPLETED - January 29, 2025)

#### Changes Made:
1. **Removed API endpoint** `/api/platzsuchen/{id}/kontaktanfrage`
2. **Removed database field** `gesamt_angeforderte_kontakte`
3. **Removed method** `update_contact_count()`
4. **Created and executed migration** `006_remove_kontaktanfrage.py`
5. **Updated tests** to reflect new schema

### Files Modified
```
matching_service/
├── api/
│   ├── __init__.py
│   └── anfrage.py
├── app.py
├── models/
│   └── platzsuche.py
└── services.py

tests/integration/
├── test_database_schemas.py
└── test_matching_service_api.py

migrations/alembic/versions/
└── 006_remove_kontaktanfrage.py
```

### ⚠️ BREAKING CHANGES INTRODUCED
- Endpoint `/api/platzsuchen/{id}/kontaktanfrage` returns 404
- Fields `gesamt_angeforderte_kontakte` and `ausgeschlossene_therapeuten_anzahl` removed from responses

---

## Feature 3: Enhanced Patient Success Email System ✅ COMPLETED

### 3.1 Email Templates ✅ COMPLETED (January 29, 2025)

#### Created 4 New Templates:

1. **patient_success_email_contact.md**
   - Patient arranges meeting via email
   - Pre-written email template included
   - PDF forms as email attachments
   - Instructions to CC Curavani

2. **patient_success_phone_contact.md**
   - Patient arranges meeting via phone
   - Phone script in bullet points
   - PDF forms brought to meeting
   - Call during telefonische Erreichbarkeit

3. **patient_success_meeting_confirmation_email.md**
   - Meeting already arranged by Curavani
   - Pre-written confirmation email
   - PDF forms as email attachments
   - Meeting location auto-generated from therapist address

4. **patient_success_meeting_confirmation_phone.md**
   - Meeting already arranged by Curavani
   - Phone confirmation script in bullet points
   - PDF forms brought to meeting
   - Call during telefonische Erreichbarkeit

### 3.2 Matching Service Code Updates ✅ COMPLETED (January 29, 2025)

#### Updated `matching_service/api/anfrage.py`:

**Modified `send_patient_success_email()` function:**
- Added `template_type` parameter (default: 'email_contact')
- Added `meeting_details` parameter for confirmation templates
- Added template mapping to select correct template file
- Added meeting details to context for confirmation templates

**Updated `PlatzsucheResource.put()` method:**
- Added new parameters to parser: `email_template_type` and `meeting_details`
- Pass template type and meeting details when sending success email

### 3.3 Template Management

⚠️ **IMPORTANT**: The old `patient_success.md` template is still in use by production. 
**DO NOT DELETE YET** - See Feature 6 for safe deletion after production deployment.

---

## Feature 4: PDF Attachment System 🔄 PENDING

### 4.1 Filesystem Structure
```
/app/storage/therapist_forms/
├── {therapist_id}/
│   ├── Anamnesebogen.pdf
│   ├── Einverstaendniserklaerung.pdf
│   └── Fragebogen_Erwachsene.pdf
```

### 4.2 Therapist Service - PDF Management

#### New File: `therapist_service/utils/pdf_manager.py`
```python
import os
import re
from typing import List, Tuple
from werkzeug.utils import secure_filename

class PDFManager:
    """Manage PDF forms for therapists."""
    
    BASE_DIR = "/app/storage/therapist_forms"
    
    @staticmethod
    def sanitize_filename(filename: str, therapist_id: int) -> str:
        """Sanitize filename while keeping it recognizable."""
        # Implementation as per original plan
        
    @staticmethod
    def get_therapist_forms(therapist_id: int) -> List[str]:
        """Get list of PDF forms for a therapist."""
        # Implementation as per original plan
    
    @staticmethod
    def upload_form(therapist_id: int, file) -> Tuple[bool, str]:
        """Upload a PDF form for a therapist."""
        # Implementation as per original plan
    
    @staticmethod
    def delete_form(therapist_id: int, filename: str) -> bool:
        """Delete a PDF form."""
        # Implementation as per original plan
```

#### Add API Endpoints in `therapist_service/api/therapists.py`:
```python
class TherapistPDFResource(Resource):
    """Manage PDF forms for therapists."""
    # Implementation as per original plan

# Register in app.py:
api.add_resource(TherapistPDFResource, '/api/therapists/<int:therapist_id>/pdfs')
```

### 4.3 Communication Service - Email Attachments

#### Modify `communication_service/api/emails.py`:
- Add `attachments` parameter to email creation
- Store attachment paths in database or pass to sender

#### Modify `communication_service/utils/email_sender.py`:
- Change MIMEMultipart from 'alternative' to 'mixed'
- Add PDF attachment handling code

### 4.4 Matching Service - Success Email Enhancement

#### Update `send_patient_success_email()` in `matching_service/api/anfrage.py`:
```python
# Get therapist PDF forms
from therapist_service.utils.pdf_manager import PDFManager
pdf_files = PDFManager.get_therapist_forms(search.vermittelter_therapeut_id)
pdf_names = [os.path.basename(f) for f in pdf_files]

# Add to context
context = {
    # ... existing context ...
    'has_pdf_forms': len(pdf_files) > 0,
    'pdf_forms': pdf_names,
}

# Add attachments to email request
email_data = {
    # ... existing fields ...
    'attachments': pdf_files if len(pdf_files) > 0 else None
}
```

---

## Feature 5: API Documentation and Frontend Updates 🔄 PENDING

### 5.1 Breaking Changes from Feature 2

#### Removed:
- **Endpoint:** `POST /api/platzsuchen/{search_id}/kontaktanfrage`
- **Response fields:**
  - `gesamt_angeforderte_kontakte`
  - `ausgeschlossene_therapeuten_anzahl`

### 5.2 New Features from Feature 3

#### Updated Endpoint:
**`PUT /api/platzsuchen/{search_id}`**

New optional parameters:
```json
{
  "status": "erfolgreich",
  "vermittelter_therapeut_id": 12345,
  "email_template_type": "meeting_confirmation_email",
  "meeting_details": {
    "date": "20. Januar 2025",
    "time": "14:00 Uhr"
  }
}
```

Template types:
- `email_contact` - Patient arranges via email (default)
- `phone_contact` - Patient arranges via phone
- `meeting_confirmation_email` - Meeting arranged, confirm via email
- `meeting_confirmation_phone` - Meeting arranged, confirm via phone

### 5.3 Required Frontend Updates

1. **Remove kontaktanfrage UI:**
   - Delete "Request Additional Contacts" buttons
   - Remove kontaktanfrage API calls
   - Update TypeScript interfaces

2. **Add template selection UI:**
   - Modal/form for selecting email template type when marking as successful
   - Conditional fields for meeting details (date/time) when confirmation templates selected
   - Help text explaining each template type

3. **Update TypeScript interfaces:**
```typescript
interface PlatzsucheUpdateRequest {
  status?: string;
  vermittelter_therapeut_id?: number;
  email_template_type?: 'email_contact' | 'phone_contact' | 
                       'meeting_confirmation_email' | 'meeting_confirmation_phone';
  meeting_details?: {
    date: string;  // Formatted date
    time: string;  // Formatted time
  };
}
```

### 5.4 Documentation Updates

Update `docs/API_REFERENCE.md`:
- Remove kontaktanfrage endpoint documentation
- Update platzsuche PUT endpoint with new parameters
- Add migration guide for v2.3
- Document PDF upload endpoints (once implemented)

---

## Feature 6: Safe Deletion of Old Template 🔄 PENDING

### ⚠️ CRITICAL: Production Safety

The old `patient_success.md` template is still being used by production. Deleting it now would break production email sending.

### Safe Deletion Process:

1. **Deploy new code to production** (Features 1-3)
2. **Verify production deployment:**
   - Check logs for successful template loading
   - Send at least one test email using new templates
   - Monitor for any template-related errors
3. **Confirm old template is no longer referenced:**
   - Search codebase for any remaining references to `patient_success.md`
   - Check production logs for any attempts to load old template
4. **Create backup of old template** (just in case)
5. **Delete `shared/templates/emails/patient_success.md`**
6. **Monitor production** for 24 hours after deletion

### File to Delete:
```
shared/templates/emails/
└── patient_success.md  # DELETE only after production verification
```

---

## Testing Plan

### 3. Email Templates ✅ TESTED
- All 4 templates created and validated
- PDF conditional sections work correctly
- Gender-specific language works
- No formatting issues (double asterisks)

### 4. Matching Service Integration ✅ COMPLETED
- Template selection implemented
- Meeting details passing implemented
- Ready for testing with PDF attachments once Feature 4 is complete

### 5. PDF System 🔄 TODO
- Upload PDFs with German characters
- Test duplicate handling
- Test size limits
- Test deletion
- Test attachment in emails

### 6. End-to-End Testing 🔄 TODO
- Complete workflow for each template type
- Verify emails received correctly
- Test PDF attachments
- Frontend integration testing

---

## Deployment Order

### Phase 1: Backend Updates (Current)
1. ✅ Deploy Features 1 & 2 (completed)
2. ✅ Deploy Feature 3 code and templates (completed)
3. ✅ Test in dev/staging environment

### Phase 2: Production Deployment
4. 🔄 Deploy updated matching service to production
5. 🔄 Verify new templates work in production
6. 🔄 Monitor for 24-48 hours

### Phase 3: PDF System
7. 🔄 Create PDF storage directory with permissions
8. 🔄 Deploy PDF management system (Feature 4)
9. 🔄 Update communication service for attachments
10. 🔄 Test PDF attachments in staging

### Phase 4: Frontend & Documentation
11. 🔄 Update API documentation (Feature 5)
12. 🔄 Deploy frontend updates
13. 🔄 Test frontend integration

### Phase 5: Cleanup
14. 🔄 Delete old template (Feature 6) - ONLY after production verification
15. 🔄 Final testing and verification

---

## Current Status Summary

### ✅ Completed:
- Feature 1: Email formatting fixes
- Feature 2: Legacy code removal
- Feature 3: Enhanced email templates (except old template deletion)
- 4 new email templates created and deployed
- Matching service code updated to support template selection

### 🔄 In Progress:
- Testing new template selection in dev/staging

### 📋 Next Steps:
1. Test template selection functionality thoroughly
2. Begin Feature 4 (PDF attachment system)
3. Prepare for production deployment
4. DO NOT delete old template until after production verification

---

## Environment Variables Required

No new environment variables needed for Features 1-3.

Feature 4 will use existing storage paths.

---

## Rollback Plan

### For Features 1-3:
1. **Templates**: Old `patient_success.md` remains as automatic fallback
2. **Code**: Git revert matching service changes if needed
3. **Database**: No schema changes, so no rollback needed

### For Feature 4 (when implemented):
1. **PDFs**: Remove PDF endpoints and storage
2. **Code**: Revert communication service changes

### For Feature 5:
1. **Frontend**: Revert to previous version without template selection

---

## Risk Assessment

### Low Risk:
- Features 1-3: Code is backward compatible with old template still present

### Medium Risk:
- Feature 4: New functionality, but isolated to specific services
- Feature 5: Frontend changes require coordination

### High Risk:
- Feature 6: Deleting old template too early could break production
  - **Mitigation**: Strict verification process before deletion

---

## Contact

For questions about this implementation, contact the backend team.

---

## Change Log

- **v4.0 (Jan 29, 2025)**: 
  - Completed Feature 3 implementation
  - Moved old template deletion to Feature 6 for production safety
  - Added detailed deployment phases and risk assessment
- **v3.0 (Jan 29, 2025)**: Feature 1, 2, and 3.1 completed
- **v2.0 (Jan 28, 2025)**: Initial comprehensive plan
