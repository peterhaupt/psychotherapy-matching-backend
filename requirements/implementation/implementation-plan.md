# PDF Attachment Support - Implementation Summary
**Date:** September 11, 2025  
**Feature:** Email PDF Attachments for Communication Service

## Overview
Successfully implemented PDF attachment support for the communication service, allowing emails to include PDF documents (e.g., therapy request forms) as attachments.

---

## 1. Database Changes

### Migration File: `007_add_email_attachments.py`
- **Location:** `migrations/alembic/versions/007_add_email_attachments.py`
- **Changes:**
  - Added `attachments` column (JSONB type) to `communication_service.emails` table
  - Created GIN index for efficient JSONB queries
  - Properly linked to previous migration (006_remove_kontaktanfrage)

```sql
-- Column added
attachments JSONB NULL

-- Index created
CREATE INDEX ix_communication_service_emails_attachments 
ON communication_service.emails USING gin(attachments);
```

---

## 2. Model Changes

### File: `communication_service/models/email.py`
- **Line 77:** Added attachments field
```python
from sqlalchemy.dialects.postgresql import JSONB

# PDF attachments support
attachments = Column(JSONB)
```

---

## 3. API Changes

### File: `communication_service/api/emails.py`

#### A. Field Definition (Line 67)
```python
# Output fields definition - FIXED after marshal error
email_fields = {
    # ... other fields ...
    'attachments': fields.Raw,  # Changed from fields.List(fields.String())
}
```
**Note:** Using `fields.Raw` to handle JSONB data properly during marshaling

#### B. POST Endpoint Updates (Lines 370-385)
```python
# Added to request parser
parser.add_argument('attachments', type=list, location='json')

# Validation for attachments
if args.get('attachments'):
    for attachment_path in args['attachments']:
        if not isinstance(attachment_path, str):
            return {'message': f'Invalid attachment path: {attachment_path}'}, 400
```

#### C. Email Creation (Lines 495-510)
```python
# Store attachments if provided (as JSON string)
if args.get('attachments'):
    if hasattr(email, 'attachments'):
        email.attachments = json.dumps(args['attachments'])
```

#### D. GET Endpoint Updates (Lines 115-130)
```python
# Parse attachments if stored as JSON string
if hasattr(email, 'attachments') and email.attachments:
    if isinstance(email.attachments, str):
        try:
            email_data['attachments'] = json.loads(email.attachments)
        except:
            email_data['attachments'] = []
    else:
        email_data['attachments'] = email.attachments
else:
    email_data['attachments'] = []
```

---

## 4. Email Sender Changes

### File: `communication_service/utils/email_sender.py`

#### A. Import Additions (Lines 8-11)
```python
import os
from email.mime.base import MIMEBase
from email import encoders
```

#### B. New Attachment Function (Lines 52-94)
```python
def _attach_pdf(msg: MIMEMultipart, file_path: str) -> bool:
    """Attach a PDF file to the email."""
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            logger.error(f"PDF file not found: {file_path}")
            return False
        
        # Check file size (limit to 10MB)
        file_size = os.path.getsize(file_path)
        if file_size > 10 * 1024 * 1024:  # 10MB
            logger.error(f"PDF file too large: {file_path} ({file_size} bytes)")
            return False
        
        # Read and attach the PDF
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
        logger.info(f"Successfully attached PDF: {filename}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to attach PDF {file_path}: {str(e)}")
        return False
```

#### C. Updated send_email Function (Lines 96-175)
- Added `attachments` parameter (Optional[List[str]])
- Changed message type to `MIMEMultipart('mixed')` to support attachments
- Added attachment processing loop:
```python
# Add PDF attachments if provided
attachment_count = 0
if attachments:
    logger.info(f"Processing {len(attachments)} attachments for email to {to_email}")
    for attachment_path in attachments:
        if attachment_path and isinstance(attachment_path, str):
            if _attach_pdf(msg, attachment_path):
                attachment_count += 1
            else:
                logger.warning(f"Failed to attach: {attachment_path}")
```

#### D. Updated send_queued_emails Function (Lines 225-245)
```python
# Parse attachments if stored as JSON
attachments = None
if hasattr(email, 'attachments') and email.attachments:
    if isinstance(email.attachments, list):
        attachments = email.attachments
    elif isinstance(email.attachments, str):
        # If stored as JSON string
        import json
        try:
            attachments = json.loads(email.attachments)
        except:
            attachments = None

# Pass attachments to send_email
success = send_email(
    # ... other parameters ...
    attachments=attachments
)
```

---

## 5. Docker Configuration Fix

### File: `docker-compose.dev.yml`
**Issue:** Communication service couldn't access PDF files created by therapist service

**Solution:** Add volume mount to communication_service (Line ~291):
```yaml
communication_service:
  volumes:
    - ./communication_service:/app
    - ./shared:/app/shared
    - ./data/therapist_pdfs:/data/therapist_pdfs  # ADDED: Access to PDF files
```

---

## 6. Issues Encountered and Resolutions

### Issue 1: Marshal Error
**Error:** `AttributeError: 'String' object has no attribute 'nested'`
**Cause:** `fields.List(fields.String)` - missing parentheses
**Initial Fix Attempt:** Changed to `fields.List(fields.String())`
**Final Solution:** Changed to `fields.Raw` to handle JSONB data properly

### Issue 2: PDF File Not Found
**Error:** `PDF file not found: /data/therapist_pdfs/development/102/...`
**Cause:** Communication service container didn't have access to PDF directory
**Solution:** Added volume mount in docker-compose.dev.yml

---

## 7. Testing Instructions

### A. Apply Database Migration
```bash
# From project root
alembic upgrade head
```

### B. Restart Services
```bash
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.dev.yml up -d
```

### C. Test API Call
```bash
curl -X POST http://localhost:8004/api/emails \
  -H "Content-Type: application/json" \
  -d '{
    "therapist_id": 102,
    "betreff": "Test Email with PDF",
    "inhalt_markdown": "Please find the attached document.",
    "empfaenger_email": "test@example.com",
    "empfaenger_name": "Test Therapist",
    "attachments": [
      "/data/therapist_pdfs/development/102/Therapieanfrage_Praxis_Test.pdf"
    ],
    "status": "In_Warteschlange"
  }'
```

---

## 8. File Structure

```
project_root/
├── migrations/
│   └── alembic/
│       └── versions/
│           └── 007_add_email_attachments.py  # NEW
├── communication_service/
│   ├── models/
│   │   └── email.py                         # MODIFIED
│   ├── api/
│   │   └── emails.py                        # MODIFIED
│   └── utils/
│       └── email_sender.py                  # MODIFIED
├── docker-compose.dev.yml                   # MODIFIED
└── data/
    └── therapist_pdfs/                      # PDF storage location
        └── development/
            └── [therapist_id]/
                └── *.pdf

```

---

## 9. Summary of Changes

1. **Database:** Added JSONB column for attachments with GIN index
2. **Model:** Added attachments field to Email model
3. **API:** 
   - Added attachment support in POST endpoint
   - Proper JSON handling in GET endpoint
   - Fixed field marshaling issue
4. **Email Sender:**
   - New PDF attachment function with size validation
   - Updated email structure to support mixed content
   - Attachment processing in queue
5. **Docker:** Added volume mount for PDF access
6. **Total Lines Changed:** ~300 lines across 4 files

---

## 10. Future Considerations

1. **File Validation:** Consider adding more robust file type validation
2. **Storage:** Consider moving PDFs to object storage (S3/Swift) for scalability
3. **Size Limits:** Current limit is 10MB per file - may need adjustment
4. **Multiple File Types:** Currently PDF-only, could extend to other document types
5. **Async Processing:** For large attachments, consider async processing
6. **Cleanup:** Implement cleanup for orphaned PDF files

---

## Deployment Checklist

- [ ] Run migration 007_add_email_attachments
- [ ] Update docker-compose configuration
- [ ] Verify PDF directory permissions
- [ ] Test with actual PDF files
- [ ] Monitor email queue for attachment processing
- [ ] Check SMTP server attachment size limits
- [ ] Update API documentation

---

**Implementation Status:** ✅ COMPLETE  
**Testing Status:** ⚠️ PARTIAL (needs production testing)  
**Documentation Status:** ✅ COMPLETE
