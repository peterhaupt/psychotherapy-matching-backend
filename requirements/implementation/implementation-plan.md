# Complete Implementation Plan
## Email Templates, PDF Attachments, and Matching Service Cleanup

**Version**: 2.1  
**Date**: January 2025  
**Scope**: Backend implementation for three features  
**Last Updated**: Feature 1 completed

---

## Overview

This document provides a complete implementation plan for:
1. ✅ **COMPLETED** - Fixing email formatting issues when therapist has no title
2. Removing legacy code from matching service
3. Implementing enhanced patient success email system with 4 templates
4. Adding PDF attachment functionality for therapist forms

---

## Feature 1: Fix Email Formatting Error ✅ COMPLETED

### Problem
Email templates show double asterisks (**) when therapist has no title due to hardcoded space.

### Implementation Notes (COMPLETED)
- Fixed `patient_success.md` template with conditional checks in 4 places
- Verified `psychotherapie_anfrage.md` and `anfrage_reminder.md` were already fixed
- **REMOVED fallback behavior**: Instead of fixing the `create_default_patient_success_message` function, we removed it entirely along with the fallback behavior. If template is missing, the email will properly fail with an error.

### Files Modified
```
shared/templates/emails/
└── patient_success.md (4 fixes applied)

matching_service/api/
└── anfrage.py (removed fallback function and behavior)
```

### Code Changes Applied

#### In patient_success.md, changed FROM:
```jinja2
{{ therapist.titel }} {{ therapist.vorname }} {{ therapist.nachname }}
```

#### TO:
```jinja2
{% if therapist.titel %}{{ therapist.titel }} {% endif %}{{ therapist.vorname }} {{ therapist.nachname }}
```

#### In anfrage.py:
- Removed `create_default_patient_success_message()` function
- Modified `send_patient_success_email()` to fail properly when template is missing

---

## Feature 2: Matching Service Legacy Code Removal

### Components to Remove

#### 1. API Endpoint and Resource
**File**: `matching_service/api/anfrage.py`
- Remove entire `KontaktanfrageResource` class (approximately lines 200-300)
- Remove import from the file's imports section

**File**: `matching_service/api/__init__.py`
- Remove `KontaktanfrageResource` from imports and `__all__`

**File**: `matching_service/app.py`
- Remove route registration:
```python
# DELETE THIS LINE:
api.add_resource(KontaktanfrageResource, '/api/platzsuchen/<int:search_id>/kontaktanfrage')
```

#### 2. Database Field and Methods
**File**: `matching_service/models/platzsuche.py`
- Remove field:
```python
# DELETE THIS:
gesamt_angeforderte_kontakte = Column(Integer, nullable=False, default=0)
```
- Remove method:
```python
# DELETE THIS ENTIRE METHOD:
def update_contact_count(self, additional_contacts: int) -> None:
    """Update the total requested contacts count."""
    self.gesamt_angeforderte_kontakte += additional_contacts
    self.updated_at = datetime.utcnow()
```

#### 3. API Response Fields
**File**: `matching_service/api/anfrage.py`

In `PlatzsucheResource.get()` remove:
```python
# DELETE THIS LINE from the return statement:
"gesamt_angeforderte_kontakte": search.gesamt_angeforderte_kontakte,
```

In `PlatzsucheListResource.get()` remove from the data array return:
```python
# DELETE THIS LINE:
"ausgeschlossene_therapeuten_anzahl": len(s.ausgeschlossene_therapeuten) if s.ausgeschlossene_therapeuten else 0,
```

#### 4. Database Migration
Create migration file: `migration_remove_kontaktanfrage.sql`
```sql
-- Migration: Remove legacy contact request field
ALTER TABLE matching_service.platzsuche 
DROP COLUMN IF EXISTS gesamt_angeforderte_kontakte;
```

Run during deployment:
```bash
psql -U $DB_USER -d $DB_NAME -f migration_remove_kontaktanfrage.sql
```

#### 5. Clean Up Bundle Terminology in Comments
Files to update (search and replace in comments only):
- `matching_service/algorithms/anfrage_creator.py`
- `matching_service/models/therapeut_anfrage_patient.py`
- `matching_service/models/therapeutenanfrage.py`

Replace in comments:
- "bundle" → "anfrage"
- "Bundle" → "Anfrage"
- "Bündel" → "Anfrage"

---

## Feature 3: Enhanced Patient Success Email System

### 3.1 Email Template Types

When marking a platzsuche as successful, staff selects one of 4 templates:

1. **Standard Contact** - Patient contacts therapist independently
2. **Phone Contact** - Patient must call therapist within availability hours
3. **Email Meeting Confirmation** - Confirms specific meeting time via email
4. **Phone Meeting Confirmation** - Confirms specific meeting time via phone

### 3.2 New Email Templates

**⚠️ IMPORTANT NOTE**: The current `patient_success.md` template CANNOT be used as a base template for the new templates. The current template uses conditional logic based on whether the therapist has an email/phone (`if has_email`, `if has_phone`), but the new templates need to be explicitly selected based on the contact method chosen by staff, independent of what contact information is available for the therapist.

Create three new templates in `shared/templates/emails/`:

#### Template B: `patient_success_phone_contact.md`
```jinja2
Sehr geehrte{{ 'r Herr' if patient.geschlecht == 'männlich' else ' Frau' }} {{ patient.nachname }},

wir haben einen freien Therapieplatz für Sie gefunden bei:

**{% if therapist.titel %}{{ therapist.titel }} {% endif %}{{ therapist.vorname }} {{ therapist.nachname }}**  
{{ therapist.strasse }}  
{{ therapist.plz }} {{ therapist.ort }}  
Telefon: {{ therapist.telefon }}

Bitte rufen Sie {% if therapist.geschlecht == 'weiblich' %}die Therapeutin{% else %}den Therapeuten{% endif %} 
innerhalb der folgenden Zeiten an:

{{ phone_availability_formatted }}

{% if has_pdf_forms %}
Bitte füllen Sie die beigefügten Formulare aus und bringen Sie diese zum Erstgespräch mit:
{% for form in pdf_forms %}
- {{ form }}
{% endfor %}
{% endif %}

Mit freundlichen Grüßen
Ihr Curavani Team
```

#### Template C: `patient_success_email_confirmation.md`
```jinja2
Sehr geehrte{{ 'r Herr' if patient.geschlecht == 'männlich' else ' Frau' }} {{ patient.nachname }},

wir haben einen Termin für Sie vereinbart:

**Datum:** {{ meeting_date }}  
**Uhrzeit:** {{ meeting_time }}  
**Ort:** {{ meeting_location }}

**Bei:** {% if therapist.titel %}{{ therapist.titel }} {% endif %}{{ therapist.vorname }} {{ therapist.nachname }}

Bitte bestätigen Sie den Termin per E-Mail an: {{ therapist.email }}

{% if has_pdf_forms %}
Bitte füllen Sie die beigefügten Formulare aus und bringen Sie diese zum Termin mit:
{% for form in pdf_forms %}
- {{ form }}
{% endfor %}
{% endif %}

Mit freundlichen Grüßen
Ihr Curavani Team
```

#### Template D: `patient_success_phone_confirmation.md`
```jinja2
Sehr geehrte{{ 'r Herr' if patient.geschlecht == 'männlich' else ' Frau' }} {{ patient.nachname }},

wir haben einen Termin für Sie vereinbart:

**Datum:** {{ meeting_date }}  
**Uhrzeit:** {{ meeting_time }}  
**Ort:** {{ meeting_location }}

**Bei:** {% if therapist.titel %}{{ therapist.titel }} {% endif %}{{ therapist.vorname }} {{ therapist.nachname }}

Bitte bestätigen Sie den Termin telefonisch unter: {{ therapist.telefon }}

{% if has_pdf_forms %}
Bitte füllen Sie die beigefügten Formulare aus und bringen Sie diese zum Termin mit:
{% for form in pdf_forms %}
- {{ form }}
{% endfor %}
{% endif %}

Mit freundlichen Grüßen
Ihr Curavani Team
```

### 3.3 Modify Existing Success Email Template

Update `shared/templates/emails/patient_success.md` to include conditional PDF mention:

Add conditional section for PDF forms where appropriate in the template. If PDFs exist, mention that forms should be filled out and brought to the appointment. The exact wording to be defined during implementation.

---

## Feature 4: PDF Attachment System

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
        name, ext = os.path.splitext(filename)
        
        # Replace German umlauts
        replacements = {
            'ä': 'ae', 'ö': 'oe', 'ü': 'ue',
            'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue',
            'ß': 'ss'
        }
        for old, new in replacements.items():
            name = name.replace(old, new)
        
        # Replace problematic characters with underscore
        name = re.sub(r'[^\w\-]', '_', name)
        name = re.sub(r'_+', '_', name)  # Remove multiple underscores
        name = name.strip('_')  # Remove leading/trailing underscores
        
        # Handle duplicates
        upload_dir = os.path.join(PDFManager.BASE_DIR, str(therapist_id))
        final_name = f"{name}{ext}"
        counter = 1
        
        while os.path.exists(os.path.join(upload_dir, final_name)):
            final_name = f"{name}_{counter}{ext}"
            counter += 1
        
        return final_name
    
    @staticmethod
    def get_therapist_forms(therapist_id: int) -> List[str]:
        """Get list of PDF forms for a therapist."""
        dir_path = os.path.join(PDFManager.BASE_DIR, str(therapist_id))
        
        if not os.path.exists(dir_path):
            return []
        
        files = []
        for filename in os.listdir(dir_path):
            if filename.lower().endswith('.pdf'):
                files.append(os.path.join(dir_path, filename))
        
        return files
    
    @staticmethod
    def upload_form(therapist_id: int, file) -> Tuple[bool, str]:
        """Upload a PDF form for a therapist."""
        # Validate file
        if not file.filename.lower().endswith('.pdf'):
            return False, "Only PDF files allowed"
        
        # Check file size (5MB limit)
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > 5 * 1024 * 1024:
            return False, "File too large (max 5MB)"
        
        # Create directory
        upload_dir = os.path.join(PDFManager.BASE_DIR, str(therapist_id))
        os.makedirs(upload_dir, exist_ok=True)
        
        # Sanitize and save
        safe_filename = PDFManager.sanitize_filename(file.filename, therapist_id)
        file_path = os.path.join(upload_dir, safe_filename)
        file.save(file_path)
        
        return True, safe_filename
    
    @staticmethod
    def delete_form(therapist_id: int, filename: str) -> bool:
        """Delete a PDF form."""
        file_path = os.path.join(PDFManager.BASE_DIR, str(therapist_id), filename)
        
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    
    @staticmethod
    def get_total_size(therapist_id: int) -> int:
        """Get total size of all PDFs for a therapist in bytes."""
        total = 0
        for file_path in PDFManager.get_therapist_forms(therapist_id):
            total += os.path.getsize(file_path)
        return total
```

#### Add to `therapist_service/api/therapists.py`:
```python
from utils.pdf_manager import PDFManager

class TherapistPDFResource(Resource):
    """Manage PDF forms for therapists."""
    
    def get(self, therapist_id):
        """Get list of PDF forms for a therapist."""
        forms = PDFManager.get_therapist_forms(therapist_id)
        form_names = [os.path.basename(f) for f in forms]
        
        return {
            'therapist_id': therapist_id,
            'forms': form_names,
            'total_size': PDFManager.get_total_size(therapist_id)
        }
    
    def post(self, therapist_id):
        """Upload a PDF form."""
        if 'file' not in request.files:
            return {'message': 'No file provided'}, 400
        
        file = request.files['file']
        if file.filename == '':
            return {'message': 'No file selected'}, 400
        
        # Check total size won't exceed 20MB
        current_size = PDFManager.get_total_size(therapist_id)
        file.seek(0, os.SEEK_END)
        new_file_size = file.tell()
        file.seek(0)
        
        if current_size + new_file_size > 20 * 1024 * 1024:
            return {'message': 'Total PDF size would exceed 20MB limit'}, 400
        
        success, result = PDFManager.upload_form(therapist_id, file)
        
        if success:
            return {'message': 'PDF uploaded', 'filename': result}, 201
        else:
            return {'message': result}, 400
    
    def delete(self, therapist_id):
        """Delete a PDF form."""
        parser = reqparse.RequestParser()
        parser.add_argument('filename', required=True)
        args = parser.parse_args()
        
        if PDFManager.delete_form(therapist_id, args['filename']):
            return {'message': 'PDF deleted'}, 200
        else:
            return {'message': 'File not found'}, 404

# In app.py, add:
api.add_resource(TherapistPDFResource, '/api/therapists/<int:therapist_id>/pdfs')
```

### 4.3 Communication Service - Email Attachments

#### Modify `communication_service/api/emails.py`:
```python
# In EmailListResource.post() method, add:
parser.add_argument('attachments', type=list, location='json')  # List of file paths

# Pass to email creation:
email = Email(
    # ... existing fields ...
)

# After saving email, handle attachments
if args.get('attachments'):
    # Store attachment paths in a new JSON field or handle directly in sender
    email.attachments = args['attachments']
```

#### Modify `communication_service/utils/email_sender.py`:
```python
# Change in send_email() method:
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

# Change from 'alternative' to 'mixed' to support attachments
msg = MIMEMultipart('mixed')

# After adding text/html parts, add PDF attachments:
if attachments:  # List of file paths
    for file_path in attachments:
        if os.path.exists(file_path) and file_path.lower().endswith('.pdf'):
            with open(file_path, 'rb') as f:
                pdf = MIMEApplication(f.read(), _subtype='pdf')
                pdf.add_header('Content-Disposition', 'attachment', 
                              filename=os.path.basename(file_path))
                msg.attach(pdf)
```

### 4.4 Matching Service - Success Email Enhancement

#### Modify `matching_service/api/anfrage.py`:

In `send_patient_success_email()` function:
```python
def send_patient_success_email(db, search: Platzsuche, template_type: str = 'standard', 
                               meeting_details: dict = None) -> tuple:
    """
    template_type: 'standard', 'phone_contact', 'email_confirmation', 'phone_confirmation'
    meeting_details: {'date': '2025-01-20', 'time': '14:00', 'location': 'Praxis XYZ'}
    """
    
    # ... existing patient/therapist fetching ...
    
    # Get therapist PDF forms
    from therapist_service.utils.pdf_manager import PDFManager
    pdf_files = PDFManager.get_therapist_forms(search.vermittelter_therapeut_id)
    pdf_names = [os.path.basename(f) for f in pdf_files]
    
    # Prepare template context
    context = {
        'patient': patient,
        'therapist': therapist,
        'has_pdf_forms': len(pdf_files) > 0,
        'pdf_forms': pdf_names,
        # ... existing context ...
    }
    
    # Add meeting details for confirmation templates
    if template_type in ['email_confirmation', 'phone_confirmation'] and meeting_details:
        context['meeting_date'] = meeting_details.get('date')
        context['meeting_time'] = meeting_details.get('time')
        context['meeting_location'] = meeting_details.get('location')
    
    # Select template based on type
    template_map = {
        'standard': 'patient_success.md',
        'phone_contact': 'patient_success_phone_contact.md',
        'email_confirmation': 'patient_success_email_confirmation.md',
        'phone_confirmation': 'patient_success_phone_confirmation.md'
    }
    
    template_name = template_map.get(template_type, 'patient_success.md')
    
    # ... render template ...
    
    # Add attachments to email request
    email_data = {
        # ... existing fields ...
        'attachments': pdf_files if len(pdf_files) > 0 else None
    }
```

#### Update PUT endpoint in `PlatzsucheResource`:
```python
# Add new parameters:
parser.add_argument('email_template_type', type=str)  # Template selection
parser.add_argument('meeting_details', type=dict, location='json')  # Meeting info

# When marking as successful:
if new_status == SuchStatus.erfolgreich and search.vermittelter_therapeut_id:
    template_type = args.get('email_template_type', 'standard')
    meeting_details = args.get('meeting_details')
    
    success, email_id, error_msg = send_patient_success_email(
        db, search, template_type, meeting_details
    )
```

---

## Testing Plan

### 1. Email Formatting ✅ COMPLETED
- Create therapist with title: "Dr. Schmidt"
- Create therapist without title: "Meyer"
- Send test emails, verify no double asterisks

### 2. Legacy Code Removal
- Verify `/api/platzsuchen/{id}/kontaktanfrage` returns 404
- Check database column removed
- Verify no errors in API responses

### 3. PDF System
- Upload PDFs with German characters: "Übergabe-Formular.pdf"
- Upload duplicate names (should get _1, _2 suffix)
- Upload 6MB file (should fail)
- Upload multiple files totaling >20MB (should fail)
- Delete PDF and verify removal

### 4. Email Templates
- Test each template type with PDFs
- Test each template type without PDFs
- Verify conditional text appears correctly
- Check PDF attachments in sent emails

---

## Environment Variables Required

No new environment variables needed. Uses existing:
- `DB_*` for database
- `SMTP_*` for email sending
- Service URLs for cross-service communication

---

## Deployment Order

1. Deploy code changes
2. Run database migration
3. Create `/app/storage/therapist_forms/` directory with proper permissions
4. Test with single therapist
5. Roll out to production

---

## Rollback Plan

1. **Email formatting**: Revert template files
2. **Legacy removal**: Restore code, add column back via migration
3. **PDF system**: Remove PDF endpoints, delete storage directory
4. **Templates**: Revert to single template

---

## Notes for Frontend Team

### Platzsuche Success Modal Needs:
```javascript
{
  "status": "erfolgreich",
  "vermittelter_therapeut_id": 12345,
  "email_template_type": "email_confirmation",  // One of 4 types
  "meeting_details": {  // Only for confirmation templates
    "date": "2025-01-20",
    "time": "14:00",
    "location": "Praxis Dr. Schmidt, Hauptstr. 1, 52062 Aachen"
  }
}
```

### PDF Upload Endpoint:
```
POST /api/therapists/{id}/pdfs
Content-Type: multipart/form-data
file: [PDF file]

GET /api/therapists/{id}/pdfs
Returns: {forms: ["Anamnesebogen.pdf", ...], total_size: 2456789}

DELETE /api/therapists/{id}/pdfs?filename=Anamnesebogen.pdf
```