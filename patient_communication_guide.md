# Implementation Guide: Patient Communication Support

## Overview
This guide details the changes needed to extend the communication service to support both therapist AND patient communications. The database schema has already been updated (see updated 001_initial_setup.py), so this guide focuses on the code changes needed.

## Communication Service Changes

### 1. Update Email Model (`communication_service/models/email.py`)

```python
# Change therapist_id to nullable and add patient_id
therapist_id = Column(Integer, nullable=True)  # Changed from nullable=False
patient_id = Column(Integer, nullable=True)     # NEW field

# Add these helper properties to the Email class:
@property
def recipient_type(self):
    """Get the type of recipient (therapist or patient)."""
    return 'therapist' if self.therapist_id else 'patient'

@property
def recipient_id(self):
    """Get the ID of the recipient regardless of type."""
    return self.therapist_id or self.patient_id

def is_for_patient(self) -> bool:
    """Check if this email is for a patient."""
    return self.patient_id is not None

def is_for_therapist(self) -> bool:
    """Check if this email is for a therapist."""
    return self.therapist_id is not None
```

### 2. Update Phone Call Model (`communication_service/models/phone_call.py`)

```python
# Change therapist_id to nullable and add patient_id
therapist_id = Column(Integer, nullable=True)  # Changed from nullable=False
patient_id = Column(Integer, nullable=True)     # NEW field

# Add the same helper properties as Email model
```

### 3. Update Email API (`communication_service/api/emails.py`)

#### Modify the request parser:
```python
def post(self):
    """Create a new email."""
    parser = reqparse.RequestParser()
    # Make therapist_id optional instead of required
    parser.add_argument('therapist_id', type=int, required=False)
    # Add patient_id as optional
    parser.add_argument('patient_id', type=int, required=False)
    # Keep other fields as they are
    
    args = parser.parse_args()
    
    # Add validation logic
    if not args.get('therapist_id') and not args.get('patient_id'):
        return {'message': 'Either therapist_id or patient_id is required'}, 400
    if args.get('therapist_id') and args.get('patient_id'):
        return {'message': 'Cannot specify both therapist_id and patient_id'}, 400
```

#### Update the GET method to support filtering:
```python
def get(self):
    """Get a list of emails with optional filtering and pagination."""
    # Existing parameters
    therapist_id = request.args.get('therapist_id', type=int)
    # Add new parameters
    patient_id = request.args.get('patient_id', type=int)
    recipient_type = request.args.get('recipient_type')  # 'therapist' or 'patient'
    
    # Apply filters
    if recipient_type == 'therapist' and therapist_id:
        query = query.filter(Email.therapist_id == therapist_id)
    elif recipient_type == 'patient' and patient_id:
        query = query.filter(Email.patient_id == patient_id)
    elif therapist_id:  # Backward compatibility
        query = query.filter(Email.therapist_id == therapist_id)
    elif patient_id:
        query = query.filter(Email.patient_id == patient_id)
```

### 4. Update Phone Call API (`communication_service/api/phone_calls.py`)

Apply the same changes as for emails:
- Make therapist_id optional
- Add patient_id field
- Add validation logic
- Update filtering in GET method

### 5. Update Email Templates (Optional)

Create patient-specific templates in `communication_service/templates/emails/`:
- `patient_welcome.html` - Welcome email for new patients
- `patient_status_update.html` - Search status updates
- `patient_match_found.html` - Therapist acceptance notification

### 6. Update Event Consumers (`communication_service/events/consumers.py`)

No changes needed - the service will continue to receive the same events, but now can handle both patient and therapist IDs.

## Patient Service Changes

### 1. Add Communication Tracking Endpoint (Optional)

If you want a dedicated endpoint for patient communication history:

```python
# In patient_service/api/patients.py
class PatientCommunicationResource(Resource):
    """REST resource for patient communication history."""
    
    def get(self, patient_id):
        """Get communication history for a patient."""
        # Verify patient exists
        db = SessionLocal()
        try:
            patient = db.query(Patient).filter(Patient.id == patient_id).first()
            if not patient:
                return {'message': 'Patient not found'}, 404
        finally:
            db.close()
        
        # Call communication service to get emails and calls
        comm_service_url = config.get_service_url('communication', internal=True)
        
        # Get emails
        email_response = requests.get(
            f"{comm_service_url}/api/emails",
            params={'patient_id': patient_id}
        )
        
        # Get phone calls
        call_response = requests.get(
            f"{comm_service_url}/api/phone-calls",
            params={'patient_id': patient_id}
        )
        
        return {
            'patient_id': patient_id,
            'emails': email_response.json() if email_response.ok else [],
            'phone_calls': call_response.json() if call_response.ok else [],
            'last_contact': patient.letzter_kontakt
        }

# In patient_service/app.py
api.add_resource(PatientCommunicationResource, 
                 '/api/patients/<int:patient_id>/communication')
```

### 2. Add Helper Functions for Communication

Create `patient_service/utils/communication.py`:

```python
import requests
from datetime import datetime
from shared.config import get_config

config = get_config()

def send_patient_email(patient_id: int, subject: str, body_html: str, body_text: str) -> bool:
    """Send an email to a patient via the communication service."""
    # Get patient data
    from models.patient import Patient
    from shared.utils.database import SessionLocal
    
    db = SessionLocal()
    try:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient or not patient.email:
            return False
        
        # Update last contact
        patient.letzter_kontakt = datetime.utcnow().date()
        db.commit()
        
        # Send via communication service
        comm_url = config.get_service_url('communication', internal=True)
        response = requests.post(
            f"{comm_url}/api/emails",
            json={
                'patient_id': patient_id,
                'betreff': subject,
                'inhalt_html': body_html,
                'inhalt_text': body_text,
                'empfaenger_email': patient.email,
                'empfaenger_name': f"{patient.vorname} {patient.nachname}"
            }
        )
        
        return response.ok
    finally:
        db.close()

def schedule_patient_call(patient_id: int, notes: str) -> bool:
    """Schedule a phone call with a patient."""
    # Similar implementation for phone calls
    pass
```

## Example Usage After Implementation

### Create Patient Email
```bash
curl -X POST http://localhost:8004/api/emails \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": 30,
    "betreff": "Update zu Ihrer Therapieplatzsuche",
    "inhalt_html": "<p>Gute Nachrichten...</p>",
    "inhalt_text": "Gute Nachrichten...",
    "empfaenger_email": "patient@example.com",
    "empfaenger_name": "Max Mustermann"
  }'
```

### Get Patient Communication History
```bash
# Get all emails for a patient
curl "http://localhost:8004/api/emails?patient_id=30"

# Get all phone calls for a patient
curl "http://localhost:8004/api/phone-calls?patient_id=30"

# Get full communication history (if endpoint added)
curl "http://localhost:8001/api/patients/30/communication"
```

### Create Bundle Email (Still Works)
```bash
curl -X POST http://localhost:8004/api/emails \
  -H "Content-Type: application/json" \
  -d '{
    "therapist_id": 123,
    "betreff": "Therapieanfrage für 3 Patienten",
    "inhalt_html": "<p>Bundle information...</p>",
    "inhalt_text": "Bundle information...",
    "empfaenger_email": "therapist@example.com",
    "empfaenger_name": "Dr. Schmidt"
  }'
```

## Testing the Implementation

1. **Test Email Creation**:
   - Create email with only patient_id ✓
   - Create email with only therapist_id ✓
   - Try to create with both (should fail) ✗
   - Try to create with neither (should fail) ✗

2. **Test Filtering**:
   - Filter emails by patient_id
   - Filter emails by therapist_id
   - Filter by recipient_type

3. **Test Phone Calls**:
   - Same tests as emails

4. **Test Patient Service Integration**:
   - Verify letzter_kontakt updates when email sent
   - Test communication history endpoint (if added)

## Migration Notes

- The database schema already supports this via the updated migration
- Existing data will continue to work (all existing emails have therapist_id)
- No data migration needed since this is a development system

## Benefits

1. **Unified Communication Tracking** - All communications in one service
2. **Consistent APIs** - Same patterns for both recipient types
3. **Audit Trail** - Complete history of all communications
4. **Reusable Templates** - Can use same email infrastructure
5. **Future-Proof** - Easy to add SMS or other channels later