# Complete Implementation Plan - UPDATED
## Email Templates, PDF Attachments, and Matching Service Cleanup

**Version**: 3.0  
**Date**: January 2025  
**Scope**: Backend implementation for five features  
**Last Updated**: January 29, 2025 - Features 1, 2, and 3.1 completed

---

## Overview

This document provides a complete implementation plan for:
1. ✅ **COMPLETED** - Fixing email formatting issues when therapist has no title
2. ✅ **COMPLETED** - Removing legacy code from matching service
3. **IN PROGRESS** - Implementing enhanced patient success email system with 4 templates
4. **PENDING** - Adding PDF attachment functionality for therapist forms
5. **PENDING** - API documentation and frontend updates for breaking changes

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

## Feature 3: Enhanced Patient Success Email System

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

#### Key Design Decisions:
- Email templates: PDF forms attached to email ("Die ausgefüllten Formulare sind im Anhang")
- Phone templates: PDF forms brought to meeting
- Meeting location: Auto-generated as `Praxis [Title] [Lastname]` with full address
- Removed: Cancellation options and "if you don't get along" text
- Phone timing: "Während der nächsten telefonischen Erreichbarkeit" instead of "Sofort"

### 3.2 Matching Service Code Updates 🔄 NEXT STEP

#### File: `matching_service/api/anfrage.py`

**Update `send_patient_success_email()` function:**
```python
def send_patient_success_email(
    db, 
    search: Platzsuche, 
    template_type: str = 'email_contact',  # New parameter
    meeting_details: dict = None  # New parameter
) -> tuple:
    """
    template_type options:
    - 'email_contact': Patient contacts via email
    - 'phone_contact': Patient contacts via phone
    - 'meeting_confirmation_email': Meeting arranged, confirm via email
    - 'meeting_confirmation_phone': Meeting arranged, confirm via phone
    
    meeting_details (only for confirmation templates):
    {
        'date': '20. Januar 2025',  # Formatted date
        'time': '14:00 Uhr'         # Formatted time
    }
    """
    
    # ... existing patient/therapist fetching ...
    
    # Map template types to files
    template_map = {
        'email_contact': 'patient_success_email_contact.md',
        'phone_contact': 'patient_success_phone_contact.md',
        'meeting_confirmation_email': 'patient_success_meeting_confirmation_email.md',
        'meeting_confirmation_phone': 'patient_success_meeting_confirmation_phone.md'
    }
    
    template_name = template_map.get(template_type, 'patient_success_email_contact.md')
    
    # Add meeting details to context if provided
    if meeting_details and template_type.startswith('meeting_confirmation'):
        context['meeting_date'] = meeting_details.get('date')
        context['meeting_time'] = meeting_details.get('time')
        # Note: meeting_location is auto-generated in template from therapist address
    
    # ... rest of function ...
```

**Update `PlatzsucheResource.put()` method:**
```python
# Add new parameters to parser
parser.add_argument('email_template_type', type=str)  # Template selection
parser.add_argument('meeting_details', type=dict, location='json')  # Meeting info

# When marking as successful:
if new_status == SuchStatus.erfolgreich and search.vermittelter_therapeut_id:
    template_type = args.get('email_template_type', 'email_contact')
    meeting_details = args.get('meeting_details')
    
    success, email_id, error_msg = send_patient_success_email(
        db, search, template_type, meeting_details
    )
```

### 3.3 Remove Old Template 🔄 NEXT STEP

Delete the old combined template:
```
shared/templates/emails/
└── patient_success.md  # DELETE this file
```

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

## Testing Plan

### 3. Email Templates ✅ TESTED
- All 4 templates created and validated
- PDF conditional sections work correctly
- Gender-specific language works
- No formatting issues (double asterisks)

### 4. Matching Service Integration 🔄 TODO
- Test template selection
- Test meeting details passing
- Test PDF attachment inclusion
- Test email sending with each template

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

1. ✅ Deploy Features 1 & 2 (already completed)
2. 🔄 Deploy Feature 3 templates to `shared/templates/emails/`
3. 🔄 Update matching service code for template selection
4. 🔄 Create PDF storage directory with permissions
5. 🔄 Deploy PDF management system
6. 🔄 Update communication service for attachments
7. 🔄 Update API documentation
8. 🔄 Deploy frontend updates
9. 🔄 Test in staging
10. 🔄 Roll out to production

---

## Next Immediate Steps

1. **Copy new templates** to `shared/templates/emails/`:
   - patient_success_email_contact.md
   - patient_success_phone_contact.md
   - patient_success_meeting_confirmation_email.md
   - patient_success_meeting_confirmation_phone.md

2. **Update matching service** (`matching_service/api/anfrage.py`):
   - Modify `send_patient_success_email()` function
   - Update `PlatzsucheResource.put()` method

3. **Delete old template**:
   - Remove `shared/templates/emails/patient_success.md`

4. **Test template selection**:
   - Test each template type
   - Verify meeting details work for confirmation templates

5. **Begin PDF system implementation**:
   - Create PDFManager class
   - Add therapist service endpoints
   - Update communication service

---

## Environment Variables Required

No new environment variables needed for Features 1-3.

Feature 4 will use existing storage paths.

---

## Notes for Next Session

- Templates are complete and ready for integration
- Next focus: Update matching service code to use new templates
- Then: Implement PDF attachment system
- Finally: Update frontend for template selection UI

---

## Rollback Plan

1. **Templates**: Keep old `patient_success.md` as backup
2. **Code**: Git revert matching service changes
3. **PDFs**: Remove PDF endpoints and storage
4. **Frontend**: Revert to previous version without template selection

---

## Contact

For questions about this implementation, contact the backend team.