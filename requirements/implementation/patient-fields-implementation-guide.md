# Implementation Guide: Automatic Patient Field Updates

## Development System Notice

**⚠️ This guide is for a DEVELOPMENT SYSTEM. No rollback procedures or production safeguards are necessary at this stage.**

**Development Environment Benefits:**
- Can make breaking changes without concern
- Database can be reset if needed
- No need for backwards compatibility
- Can test edge cases aggressively
- Kafka topics can be recreated/cleared as needed

## Overview

This document outlines the implementation of three key changes to the patient management system:

1. **Startdatum Therapiesuche**: Automatically set when both prerequisites are met
2. **letzter_kontakt**: Automatically updated based on successful communications via Kafka events
3. **bevorzugtes_therapieverfahren**: Validation to ensure only allowed enum values

## 1. Startdatum Therapiesuche (Therapy Search Start Date)

### Business Logic
- Set automatically to the current date when BOTH conditions are first met:
  - `vertraege_unterschrieben` = true
  - `psychotherapeutische_sprechstunde` = true
- Once set, the date remains unchanged even if the checkboxes are later unchecked
- Cannot be manually set via API

### Implementation

#### File: `patient_service/api/patients.py`

**In `PatientResource.put()` method:**

1. Before processing updates, check current patient state
2. After setting new values, check if conditions are met
3. If both conditions are true AND startdatum is None, set it to today

```python
# In the PUT method, after fetching the patient:
original_vertraege = patient.vertraege_unterschrieben
original_sprechstunde = patient.psychotherapeutische_sprechstunde
original_startdatum = patient.startdatum

# Process updates (existing code)
for key, value in args.items():
    if value is not None:
        # Skip manual setting of startdatum
        if key == 'startdatum':
            continue  # Ignore client-provided startdatum
        # ... rest of existing update logic

# After all updates, check if we need to set startdatum
if (patient.vertraege_unterschrieben and 
    patient.psychotherapeutische_sprechstunde and 
    patient.startdatum is None):
    patient.startdatum = date.today()
```

**In `PatientListResource.post()` method:**

1. Remove `startdatum` from accepted arguments
2. After creating patient, check conditions and set if needed

```python
# Remove from parser:
# parser.add_argument('startdatum', type=str)  # Remove this line

# After creating patient object, before db.add():
if (patient.vertraege_unterschrieben and 
    patient.psychotherapeutische_sprechstunde):
    patient.startdatum = date.today()
```

## 2. letzter_kontakt (Last Contact Date)

### Business Logic
- Updated automatically when successful communication occurs:
  - Email sent successfully (status = "Gesendet")
  - Email response received (antwort_erhalten = true)
  - Phone call completed (status = "abgeschlossen")
- Uses Kafka event-driven architecture
- Cannot be manually set via API

### Implementation

#### Communication Service Changes

##### File: `communication_service/events/__init__.py` (NEW)
```python
"""Event producers for the Communication Service."""
from .producers import (
    publish_email_sent,
    publish_email_response_received,
    publish_phone_call_completed
)

__all__ = [
    'publish_email_sent',
    'publish_email_response_received',
    'publish_phone_call_completed',
]
```

##### File: `communication_service/events/producers.py` (NEW)
```python
"""Producer for communication-related Kafka events."""
import logging
from typing import Dict, Any
from shared.kafka.robust_producer import RobustKafkaProducer

logger = logging.getLogger(__name__)
producer = RobustKafkaProducer(service_name="communication-service")
COMMUNICATION_TOPIC = "communication-events"

def publish_email_sent(patient_id: int = None, therapist_id: int = None, 
                      email_id: int = None) -> bool:
    """Publish event when email is sent successfully."""
    return producer.send_event(
        topic=COMMUNICATION_TOPIC,
        event_type="email.sent",
        payload={
            "patient_id": patient_id,
            "therapist_id": therapist_id,
            "email_id": email_id,
            "communication_type": "email"
        },
        key=str(patient_id or therapist_id)
    )

def publish_email_response_received(patient_id: int = None, therapist_id: int = None,
                                   email_id: int = None) -> bool:
    """Publish event when email response is received."""
    return producer.send_event(
        topic=COMMUNICATION_TOPIC,
        event_type="email.response_received",
        payload={
            "patient_id": patient_id,
            "therapist_id": therapist_id,
            "email_id": email_id,
            "communication_type": "email"
        },
        key=str(patient_id or therapist_id)
    )

def publish_phone_call_completed(patient_id: int = None, therapist_id: int = None,
                                call_id: int = None) -> bool:
    """Publish event when phone call is completed."""
    return producer.send_event(
        topic=COMMUNICATION_TOPIC,
        event_type="phone_call.completed",
        payload={
            "patient_id": patient_id,
            "therapist_id": therapist_id,
            "call_id": call_id,
            "communication_type": "phone_call"
        },
        key=str(patient_id or therapist_id)
    )
```

##### File: `communication_service/api/emails.py`

Add event publishing at appropriate points:

```python
# When email status changes to "Gesendet"
if email.status == EmailStatus.Gesendet:
    publish_email_sent(
        patient_id=email.patient_id,
        therapist_id=email.therapist_id,
        email_id=email.id
    )

# When antwort_erhalten is set to True
if data.get('antwort_erhalten') and not email.antwort_erhalten:
    email.antwort_erhalten = True
    # ... other updates
    publish_email_response_received(
        patient_id=email.patient_id,
        therapist_id=email.therapist_id,
        email_id=email.id
    )
```

##### File: `communication_service/api/phone_calls.py`

Add event publishing when call is completed:

```python
# When phone call status changes to "abgeschlossen"
if call.status == CallStatus.abgeschlossen:
    publish_phone_call_completed(
        patient_id=call.patient_id,
        therapist_id=call.therapist_id,
        call_id=call.id
    )
```

#### Patient Service Changes

##### File: `patient_service/events/consumers.py`

Add new handler:

```python
from datetime import date
from models.patient import Patient
from shared.utils.database import SessionLocal

def handle_communication_event(event: EventSchema) -> None:
    """Handle communication events to update letzter_kontakt."""
    logger.info(f"Processing communication event: {event.event_type}")
    
    # Only process events that indicate successful communication
    if event.event_type not in ["email.sent", "email.response_received", "phone_call.completed"]:
        return
    
    patient_id = event.payload.get("patient_id")
    if not patient_id:
        return  # Skip if no patient involved
    
    db = SessionLocal()
    try:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if patient:
            patient.letzter_kontakt = date.today()
            db.commit()
            logger.info(f"Updated letzter_kontakt for patient {patient_id}")
    except Exception as e:
        logger.error(f"Error updating letzter_kontakt: {str(e)}")
        db.rollback()
    finally:
        db.close()

def start_consumers():
    """Start all Kafka consumers for the Patient Service."""
    try:
        from shared.kafka import KafkaConsumer
        import threading
        
        # Consumer for communication events
        comm_consumer = KafkaConsumer(
            topics=["communication-events"],
            group_id="patient-service-comm",
        )
        
        comm_event_types = ["email.sent", "email.response_received", "phone_call.completed"]
        
        thread = threading.Thread(
            target=comm_consumer.process_events,
            args=(handle_communication_event, comm_event_types),
            daemon=True
        )
        thread.start()
        
        logger.info("Communication event consumer started")
    except Exception as e:
        logger.error(f"Failed to start Kafka consumers: {str(e)}")
```

##### File: `patient_service/app.py`

Add consumer initialization:

```python
# Add import
from events.consumers import start_consumers

# In create_app(), before return:
# Start Kafka consumers
start_consumers()
```

##### File: `patient_service/api/patients.py`

Prevent manual setting of letzter_kontakt:

```python
# In both POST and PUT methods, skip letzter_kontakt
if key == 'letzter_kontakt':
    continue  # Ignore client-provided letzter_kontakt
```

## 3. bevorzugtes_therapieverfahren Validation

### Business Logic
- Only accept valid enum values: "egal", "Verhaltenstherapie", "tiefenpsychologisch_fundierte_Psychotherapie"
- Return 400 error with clear message for invalid values
- Ensure array handling is consistent

### Implementation

#### File: `patient_service/api/patients.py`

Add validation function:

```python
def validate_therapieverfahren_array(verfahren_list: list) -> list:
    """Validate array of Therapieverfahren values.
    
    Args:
        verfahren_list: List of therapy method strings
        
    Returns:
        List of validated Therapieverfahren enum values
        
    Raises:
        ValueError: If any value is invalid
    """
    if not verfahren_list:
        return []
    
    valid_values = ["egal", "Verhaltenstherapie", "tiefenpsychologisch_fundierte_Psychotherapie"]
    validated = []
    
    for verfahren in verfahren_list:
        if verfahren not in valid_values:
            raise ValueError(
                f"Invalid therapy method '{verfahren}'. "
                f"Valid values: {', '.join(valid_values)}"
            )
        validated.append(verfahren)
    
    return validated
```

In both POST and PUT methods:

```python
# When processing bevorzugtes_therapieverfahren
elif key == 'bevorzugtes_therapieverfahren':
    try:
        validated_verfahren = validate_therapieverfahren_array(value)
        patient_data[key] = validated_verfahren  # or setattr for PUT
    except ValueError as e:
        return {'message': str(e)}, 400
```

## Frontend Changes Required

### File: `src/components/patient/PatientForm.js`

1. Remove date pickers for `startdatum` and `letzter_kontakt`
2. Display these fields as read-only with explanatory text:

```javascript
// Instead of FormInput for startdatum:
<Form.Group>
  <Form.Label>Startdatum Therapiesuche</Form.Label>
  <Form.Control
    type="text"
    value={formData.startdatum ? new Date(formData.startdatum).toLocaleDateString('de-DE') : 'Noch nicht gestartet'}
    disabled
  />
  <Form.Text className="text-muted">
    Wird automatisch gesetzt, wenn Verträge unterschrieben und Sprechstunde absolviert sind
  </Form.Text>
</Form.Group>

// Instead of FormInput for letzter_kontakt:
<Form.Group>
  <Form.Label>Letzter Kontakt</Form.Label>
  <Form.Control
    type="text"
    value={formData.letzter_kontakt ? new Date(formData.letzter_kontakt).toLocaleDateString('de-DE') : 'Kein Kontakt'}
    disabled
  />
  <Form.Text className="text-muted">
    Wird automatisch basierend auf E-Mails und Telefonaten aktualisiert
  </Form.Text>
</Form.Group>
```

3. Remove these fields from the data sent to the API in handleSubmit

## Testing Checklist

**Note: This is a development system - feel free to test extensively without concerns about production data.**

### Startdatum Tests
- [ ] Create patient with both checkboxes true → startdatum set to today
- [ ] Create patient with one/no checkboxes → startdatum remains null
- [ ] Update patient to check both boxes → startdatum set to today
- [ ] Update patient to uncheck boxes after startdatum set → date remains
- [ ] Try to manually set startdatum via API → ignored

### letzter_kontakt Tests
- [ ] Send email to patient → letzter_kontakt updated
- [ ] Receive email response → letzter_kontakt updated
- [ ] Complete phone call → letzter_kontakt updated
- [ ] Failed email/cancelled call → letzter_kontakt NOT updated
- [ ] Try to manually set letzter_kontakt via API → ignored

### bevorzugtes_therapieverfahren Tests
- [ ] Submit valid values → accepted
- [ ] Submit invalid value → 400 error with clear message
- [ ] Submit empty array → accepted
- [ ] Submit mix of valid/invalid → 400 error

## Deployment Considerations (Development Environment)

1. **Database Migration**: No schema changes required
2. **Kafka Topics**: Ensure "communication-events" topic exists in development
3. **Service Dependencies**: Deploy Communication Service changes before Patient Service
4. **Frontend**: Can be deployed independently after backend

## Development Testing Notes

Since this is a development system:
- Feel free to test edge cases aggressively
- No need to worry about data integrity during testing
- Can reset database if needed
- Kafka events can be replayed or cleared as necessary

---

End of Implementation Guide