# Communication Service

> **Note**: For complete API documentation, see `API_REFERENCE.md`

## Summary
Handles all communications (emails and phone calls) for BOTH therapists and patients. Simplified architecture with bundle logic moved to Matching Service.

## Current Status ✅ FULLY UPDATED
- **Dual Recipient Support**: All models and APIs support both therapist_id AND patient_id
- **Constraint Validation**: Database enforces exactly one recipient type per communication
- **German Field Names**: Complete consistency across models and APIs
- **Bundle Logic Removed**: Service focuses solely on communication delivery

## Models (with Dual Support)

### Email Model (`models/email.py`)
```python
# Key fields (German names)
therapist_id = Column(Integer, nullable=True)  # Either this...
patient_id = Column(Integer, nullable=True)    # ...OR this (not both)
betreff, empfaenger_email, empfaenger_name     # German field names
status = EmailStatus (German enum values)
```

### PhoneCall Model (`models/phone_call.py`)
```python
# Key fields (German names)  
therapist_id = Column(Integer, nullable=True)  # Either this...
patient_id = Column(Integer, nullable=True)    # ...OR this (not both)
geplantes_datum, geplante_zeit, dauer_minuten  # German field names
status = PhoneCallStatus (German enum values)
```

### Database Constraints
Check constraints ensure exactly one recipient type:
```sql
CHECK ((therapist_id IS NOT NULL AND patient_id IS NULL) OR 
       (therapist_id IS NULL AND patient_id IS NOT NULL))
```

## API Usage

### Creating Communications
```bash
# Email to therapist
POST /api/emails
{
  "therapist_id": 123,  # XOR with patient_id
  "betreff": "...",
  "empfaenger_email": "..."
}

# Email to patient  
POST /api/emails
{
  "patient_id": 456,   # XOR with therapist_id
  "betreff": "...",
  "empfaenger_email": "..."
}
```

### Phone Call Scheduling
- **Therapists**: Auto-scheduled based on availability
- **Patients**: Manual scheduling or defaults (tomorrow 10:00)

## Key Features

### Email System
- SMTP integration with centralized config
- HTML/text templates
- Status tracking (Entwurf → In_Warteschlange → Gesendet)
- Response tracking
- 7-day follow-up detection

### Phone Call System  
- Availability-based scheduling for therapists
- Follow-up automation
- Status tracking with German enums

### Template System
Located in `templates/`:
- Base template with responsive design
- Specialized templates (may need updates for patients)

## Integration

### With Matching Service
- Matching creates bundles
- Calls Communication API to send emails
- Stores email_id in Therapeutenanfrage

### With Patient Service
- Patient Service calls Communication API
- Updates patient's letzter_kontakt automatically
- See `patient_service/utils/communication.py`

## Events
**Publishers**: 
- `communication.email_created`
- `communication.email_sent`
- `communication.call_scheduled` 
- `communication.call_completed`

## Configuration
All via `shared.config`:
- SMTP settings (host, port, credentials)
- Default sender info
- Service URLs for cross-service calls

## Best Practices
1. **Always specify ONE recipient**: Either therapist_id OR patient_id
2. **Use German field names**: In all API requests/responses
3. **Handle null defaults**: Use `or` operator for RequestParser
4. **Update last contact**: Patient service handles this automatically