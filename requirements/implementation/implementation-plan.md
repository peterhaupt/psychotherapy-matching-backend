# Complete Implementation Plan - UPDATED
## Email Templates, PDF Attachments, and Matching Service Cleanup

**Version**: 5.0  
**Date**: January 2025  
**Scope**: Backend implementation for five features  
**Last Updated**: January 30, 2025 - Feature 4 partially completed (Therapist Service done)

---

## Overview

This document provides a complete implementation plan for:
1. ✅ **COMPLETED** - Fixing email formatting issues when therapist has no title
2. ✅ **COMPLETED** - Removing legacy code from matching service
3. ✅ **COMPLETED** - Implementing enhanced patient success email system with 4 templates
4. 🔄 **IN PROGRESS** - Adding PDF attachment functionality for therapist forms
5. **PENDING** - API documentation and frontend updates for breaking changes
6. **PENDING** - Delete old patient_success.md template (moved to end for safe deployment)

---

## Feature 1: Fix Email Formatting Error ✅ COMPLETED

### Implementation (COMPLETED - January 29, 2025)
- Fixed `patient_success.md` template with conditional checks in 4 places
- Verified other templates were already fixed
- Removed fallback function `create_default_patient_success_message()` from `anfrage.py`
- System now properly fails if template is missing instead of using fallback

---

## Feature 2: Matching Service Legacy Code Removal ✅ COMPLETED

### Implementation (COMPLETED - January 29, 2025)
- Removed API endpoint `/api/platzsuchen/{id}/kontaktanfrage`
- Removed database field `gesamt_angeforderte_kontakte`
- Removed method `update_contact_count()`
- Created and executed migration `006_remove_kontaktanfrage.py`
- Updated tests to reflect new schema

### ⚠️ BREAKING CHANGES INTRODUCED
- Endpoint `/api/platzsuchen/{id}/kontaktanfrage` returns 404
- Fields `gesamt_angeforderte_kontakte` and `ausgeschlossene_therapeuten_anzahl` removed from responses

---

## Feature 3: Enhanced Patient Success Email System ✅ COMPLETED

### Implementation (COMPLETED - January 29, 2025)
- Created 4 new email templates (email_contact, phone_contact, meeting_confirmation_email, meeting_confirmation_phone)
- Updated matching service to support template selection
- Added meeting_details parameter for confirmation templates
- Templates ready to work with PDF attachments once Feature 4 is complete

---

## Feature 4: PDF Attachment System 🔄 IN PROGRESS

### 4.1 Environment Configuration ✅ COMPLETED (January 30, 2025)

#### Files Modified:
- `.env.example` - Added `THERAPIST_PDF_STORAGE_PATH` variable
- `.env.dev` - Added environment-specific path
- `docker-compose.dev.yml` - Added volume mount and environment variable

#### Storage Structure Created:
```
data/
├── patient_imports/
│   ├── development/
│   ├── test/
│   └── production/
└── therapist_pdfs/        # NEW
    ├── development/       # NEW
    ├── test/             # NEW
    └── production/       # NEW
```

### 4.2 Therapist Service - PDF Management ✅ COMPLETED (January 30, 2025)

#### Files Created/Modified:
1. **NEW: `therapist_service/utils/pdf_manager.py`**
   - Complete PDF management class
   - Handles upload, list, delete operations
   - German filename support with proper sanitization
   - File size validation (10MB max)
   - Automatic directory management

2. **MODIFIED: `therapist_service/api/therapists.py`**
   - Added `TherapistPDFResource` class
   - Endpoints: GET (list), POST (upload), DELETE
   - Full error handling and validation

3. **MODIFIED: `therapist_service/app.py`**
   - Registered endpoint: `/api/therapists/<int:therapist_id>/pdfs`

4. **MODIFIED: `therapist_service/requirements.txt`**
   - Added `werkzeug==3.0.1` for secure filename handling

5. **MODIFIED: `therapist_service/utils/__init__.py`**
   - Added PDFManager import

### 4.3 Communication Service - Email Attachments 🔄 PENDING

#### Files to Modify:

**1. `communication_service/utils/email_sender.py`:**
```python
# Changes needed:
# - Change MIMEMultipart from 'alternative' to 'mixed'
# - Add attachment handling in create_email_message()
# - Add method to attach PDF files:

def _attach_pdf(self, msg: MIMEMultipart, file_path: str):
    """Attach a PDF file to the email."""
    try:
        with open(file_path, 'rb') as f:
            pdf_data = f.read()
        
        pdf_attachment = MIMEBase('application', 'pdf')
        pdf_attachment.set_payload(pdf_data)
        encoders.encode_base64(pdf_attachment)
        
        filename = os.path.basename(file_path)
        pdf_attachment.add_header(
            'Content-Disposition',
            f'attachment; filename="{filename}"'
        )
        
        msg.attach(pdf_attachment)
    except Exception as e:
        logger.error(f"Failed to attach PDF {file_path}: {str(e)}")
```

**2. `communication_service/api/emails.py`:**
```python
# In EmailListResource.post():
# Add to parser:
parser.add_argument('attachments', type=list, location='json')

# Pass to email creation:
if args.get('attachments'):
    # Store attachment paths or pass to sender
    email.attachments = args['attachments']
```

### 4.4 Matching Service - Success Email Enhancement 🔄 PENDING

#### File to Modify:

**`matching_service/api/anfrage.py` in `send_patient_success_email()`:**
```python
# After getting therapist data:
# Get therapist PDF forms
therapist_service_url = config.get_service_url('therapist', internal=True)
pdf_response = requests.get(
    f"{therapist_service_url}/api/therapists/{search.vermittelter_therapeut_id}/pdfs",
    timeout=5
)

pdf_files = []
pdf_names = []
if pdf_response.status_code == 200:
    pdf_data = pdf_response.json()
    for pdf_info in pdf_data.get('pdfs', []):
        pdf_files.append(pdf_info['path'])
        pdf_names.append(pdf_info['filename'])

# Add to context:
context = {
    # ... existing context ...
    'has_pdf_forms': len(pdf_files) > 0,
    'pdf_forms': pdf_names,
}

# Add attachments to email request:
email_data = {
    # ... existing fields ...
    'attachments': pdf_files if len(pdf_files) > 0 else None
}
```

---

## Feature 5: API Documentation and Frontend Updates 🔄 PENDING

### 5.1 Breaking Changes Documentation
Document all breaking changes from Feature 2 for frontend team.

### 5.2 New PDF Endpoints Documentation

#### Therapist Service:
**`GET /api/therapists/{therapist_id}/pdfs`**
- Returns list of PDF files with metadata

**`POST /api/therapists/{therapist_id}/pdfs`**
- Upload new PDF (multipart/form-data)
- Max file size: 10MB

**`DELETE /api/therapists/{therapist_id}/pdfs?filename={filename}`**
- Delete specific file or all files if no filename provided

### 5.3 Frontend Requirements
1. Add PDF upload interface in therapist management
2. Display PDF list for each therapist
3. Delete functionality for PDFs
4. Update success email preview to show attached PDFs

---

## Feature 6: Safe Deletion of Old Template 🔄 PENDING

### Process:
1. Deploy all changes to production
2. Verify new templates work
3. Monitor for 24-48 hours
4. Delete `shared/templates/emails/patient_success.md`

---

## Current Status Summary

### ✅ Completed (January 30, 2025):
- All email template fixes
- Legacy code removal from matching service
- Enhanced email template system
- PDF storage infrastructure
- Therapist service PDF management (full CRUD operations)

### 🔄 Next Steps (In Order):
1. **Communication Service Updates** (2 files)
   - `utils/email_sender.py` - Add attachment support
   - `api/emails.py` - Accept attachments parameter

2. **Matching Service Integration** (1 file)
   - `api/anfrage.py` - Fetch and attach PDFs

3. **Testing**
   - Upload PDFs with German filenames
   - Send test emails with attachments
   - Verify PDFs are readable

4. **Documentation**
   - Update API docs
   - Create frontend integration guide

5. **Production Deployment**
   - Deploy to staging first
   - Test thoroughly
   - Deploy to production
   - Delete old template after verification

---

## Testing Checklist

### PDF Upload Testing:
- [ ] Upload PDF with German characters (ä, ö, ü, ß)
- [ ] Upload PDF with spaces in filename
- [ ] Upload PDF > 10MB (should fail)
- [ ] Upload non-PDF file (should fail)
- [ ] Upload duplicate filename (should rename)

### Email Attachment Testing:
- [ ] Email with single PDF attachment
- [ ] Email with multiple PDF attachments
- [ ] Email with no attachments
- [ ] Large PDF attachment (5-10MB)

### Integration Testing:
- [ ] Complete flow: Upload PDF → Match patient → Send email with attachment
- [ ] Verify PDF is readable when received
- [ ] Test all 4 email templates with attachments

---

## Commands Reference

### Restart Services:
```bash
# After code changes
docker-compose -f docker-compose.dev.yml restart therapist_service
docker-compose -f docker-compose.dev.yml restart communication_service
docker-compose -f docker-compose.dev.yml restart matching_service
```

### Check Logs:
```bash
docker-compose -f docker-compose.dev.yml logs -f therapist_service
docker-compose -f docker-compose.dev.yml logs -f communication_service
docker-compose -f docker-compose.dev.yml logs -f matching_service
```

### Test PDF Upload (using curl):
```bash
curl -X POST -F "file=@test.pdf" \
  http://localhost:8002/api/therapists/123/pdfs
```

---

## Notes for Next Session

**Starting Point:** Implement Communication Service changes (Section 4.3)

**Files to modify:**
1. `communication_service/utils/email_sender.py`
2. `communication_service/api/emails.py`
3. `matching_service/api/anfrage.py`

**Environment is ready:** Storage paths configured, volumes mounted, therapist service complete.

---

## Contact

For questions about this implementation, contact the backend team.

---

## Change Log

- **v5.0 (Jan 30, 2025)**: 
  - Completed therapist service PDF management
  - Set up storage infrastructure
  - Ready for communication service updates
- **v4.0 (Jan 29, 2025)**: Completed Features 1-3
- **v3.0 (Jan 29, 2025)**: Feature 1, 2, and 3.1 completed
- **v2.0 (Jan 28, 2025)**: Initial comprehensive plan
