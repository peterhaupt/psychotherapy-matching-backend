# Kafka in Patient Service
## Event-Driven Architecture Documentation

---

## Overview
The Patient Service uses Apache Kafka for asynchronous, event-driven communication between microservices. It acts as both an event producer (publishing events when patient-related actions occur) and an event consumer (reacting to events from other services to update patient data).

---

## Kafka as Event Producer

The patient service publishes events to the **`patient-events`** topic to notify other services about patient-related activities.

### Published Events

#### 1. **`patient.created`**
- **Trigger**: When a new patient is registered in the system
- **Payload**:
  ```json
  {
    "patient_id": int,
    "patient_data": {
      "id": int,
      "vorname": string,
      "nachname": string,
      "email": string,
      "telefon": string,
      "plz": string,
      "status": string,
      "symptome": array,
      "zahlungsreferenz": string,
      "zahlung_eingegangen": boolean,
      // ... additional patient fields
    }
  }
  ```
- **Purpose**: Notifies other services about new patient registrations for initiating workflows

#### 2. **`patient.updated`**
- **Trigger**: When patient information is modified
- **Payload**:
  ```json
  {
    "patient_id": int,
    "patient_data": {
      // Complete updated patient object
    }
  }
  ```
- **Purpose**: Keeps other services synchronized with patient data changes

#### 3. **`patient.deleted`**
- **Trigger**: When a patient record is deleted from the system
- **Payload**:
  ```json
  {
    "patient_id": int,
    "additional_data": {
      "id": int
    }
  }
  ```
- **Purpose**: Allows other services to clean up related data

#### 4. **`patient.status_changed`**
- **Trigger**: When a patient's status changes (e.g., from "offen" to "auf_der_Suche")
- **Payload**:
  ```json
  {
    "patient_id": int,
    "old_status": string,
    "new_status": string,
    "patient_data": {
      // Complete patient object with new status
    }
  }
  ```
- **Purpose**: Triggers status-specific workflows in other services

#### 5. **`patient.therapist_excluded`**
- **Trigger**: When a patient excludes a therapist from their matching pool
- **Payload**:
  ```json
  {
    "patient_id": int,
    "therapist_id": int,
    "reason": string (optional)
  }
  ```
- **Purpose**: Updates matching algorithms to respect patient preferences

---

## Kafka as Event Consumer

The patient service consumes events from the **`communication-events`** topic to maintain accurate patient records.

### Consumed Events

#### 1. **`email.sent`**
- **Action**: Updates `letzter_kontakt` (last contact) date
- **Processing**:
  1. Extracts `patient_id` from event payload
  2. Retrieves patient from database
  3. Updates `letzter_kontakt` to current date
  4. Commits changes to database
- **Expected Payload**:
  ```json
  {
    "patient_id": int,
    "email_id": int,
    "email_data": {...}
  }
  ```

#### 2. **`email.response_received`**
- **Action**: Updates `letzter_kontakt` date when patient responds
- **Processing**:
  1. Extracts `patient_id` from event payload
  2. Updates patient's last contact date
  3. Logs the interaction
- **Expected Payload**:
  ```json
  {
    "patient_id": int,
    "email_id": int,
    "email_data": {...}
  }
  ```

#### 3. **`phone_call.completed`**
- **Action**: Updates `letzter_kontakt` date after successful phone call
- **Processing**:
  1. Extracts `patient_id` from event payload
  2. Updates patient's last contact date to today
  3. Records the communication in the patient's history
- **Expected Payload**:
  ```json
  {
    "patient_id": int,
    "call_id": int,
    "call_data": {...}
  }
  ```

### Future Consumed Events (Planned)

#### **From `therapist-events` topic** (when therapist service is implemented):

#### 1. **`therapist.blocked`**
- **Action**: Update patient records where blocked therapist is assigned
- **Processing**: Handle reassignment logic for affected patients

#### 2. **`therapist.unblocked`**
- **Action**: Re-enable therapist in matching pool for eligible patients
- **Processing**: Update availability status for matching

---

## Automated Processes

### GCS Patient Import Monitor
- **Frequency**: Configurable via `PATIENT_IMPORT_CHECK_INTERVAL_SECONDS`
- **Function**: `start_patient_import_monitor()`
- **Purpose**: Monitors Google Cloud Storage for new patient registration files
- **Process**:
  1. Scans GCS bucket for JSON files
  2. Downloads and validates patient data
  3. Creates patient record via API
  4. Publishes `patient.created` event
  5. Sends confirmation email with payment details
  6. Moves processed files to appropriate folders

### Phase 2 Automatic Transitions
- **Trigger**: Payment confirmation (`zahlung_eingegangen` changes to true)
- **Actions**:
  1. Sets `startdatum` to current date
  2. Changes status from "offen" to "auf_der_Suche"
  3. Publishes `patient.status_changed` event

---

## Implementation Details

### Producer Implementation
```python
# Located in: patient_service/events/producers.py

from shared.kafka.robust_producer import RobustKafkaProducer

producer = RobustKafkaProducer(service_name="patient-service")
PATIENT_TOPIC = "patient-events"

# Example: Publishing patient created event
def publish_patient_created(patient_id: int, patient_data: Dict[str, Any]) -> bool:
    return producer.send_event(
        topic=PATIENT_TOPIC,
        event_type="patient.created",
        payload={
            "patient_id": patient_id,
            "patient_data": patient_data
        },
        key=str(patient_id)
    )

# Example: Publishing status change event
def publish_patient_status_changed(
    patient_id: int, 
    old_status: Optional[str], 
    new_status: Optional[str], 
    patient_data: Dict[str, Any]
) -> bool:
    return producer.send_event(
        topic=PATIENT_TOPIC,
        event_type="patient.status_changed",
        payload={
            "patient_id": patient_id,
            "old_status": old_status,
            "new_status": new_status,
            "patient_data": patient_data
        },
        key=str(patient_id)
    )
```

### Consumer Implementation
```python
# Located in: patient_service/events/consumers.py

from shared.kafka import EventSchema, KafkaConsumer
from models.patient import Patient
from shared.utils.database import SessionLocal

def handle_communication_event(event: EventSchema) -> None:
    """Handle communication events to update letzter_kontakt."""
    
    # Only process events indicating successful communication
    if event.event_type not in ["email.sent", "email.response_received", "phone_call.completed"]:
        return
    
    patient_id = event.payload.get("patient_id")
    if not patient_id:
        return
    
    # Update patient's last contact date
    db = SessionLocal()
    try:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if patient:
            patient.letzter_kontakt = date.today()
            db.commit()
    finally:
        db.close()

# Start consumer
def start_consumers():
    comm_consumer = KafkaConsumer(
        topics=["communication-events"],
        group_id="patient-service-comm",
    )
    
    comm_event_types = ["email.sent", "email.response_received", "phone_call.completed"]
    
    comm_thread = threading.Thread(
        target=comm_consumer.process_events,
        args=(handle_communication_event, comm_event_types),
        daemon=True
    )
    comm_thread.start()
```

---

## Event Flow Examples

### Patient Registration Flow
1. GCS Monitor detects new JSON file
2. Patient data is imported and validated
3. Patient record created in database
4. **Event Published**: `patient.created`
5. Confirmation email sent (triggers Communication Service)
6. File moved to processed/failed folder

### Payment Confirmation Flow
1. Admin updates `zahlung_eingegangen` to true via API
2. System checks if `vertraege_unterschrieben` is also true
3. If yes, automatically sets `startdatum` to today
4. Status changes from "offen" to "auf_der_Suche"
5. **Event Published**: `patient.status_changed`
6. Matching service receives event and begins therapist search

### Communication Update Flow
1. Communication service sends email to patient
2. **Event Received**: `email.sent` from communication-events
3. Patient service updates `letzter_kontakt` field
4. Database commit confirms update
5. Updated patient data available for all services

---

## Configuration

### Environment Variables
- `KAFKA_BOOTSTRAP_SERVERS`: Kafka broker addresses
- `KAFKA_LOG_LEVEL`: Logging level for Kafka operations
- `PATIENT_IMPORT_CHECK_INTERVAL_SECONDS`: Frequency of GCS import checks
- `GCS_IMPORT_BUCKET`: Google Cloud Storage bucket name
- `PATIENT_IMPORT_LOCAL_PATH`: Local storage path for imported files

### Topics Configuration
- **Produces to**: `patient-events`
- **Consumes from**: `communication-events`
- **Future consumption**: `therapist-events` (when implemented)

---

## Error Handling

### Producer Error Handling
- Utilizes `RobustKafkaProducer` with automatic retry logic
- Failed events are logged with full context
- Non-blocking: Service continues operation even if Kafka is temporarily unavailable

### Consumer Error Handling
- Each event processed in try-catch block
- Database rollback on errors
- Failed events logged but don't stop consumption
- Automatic reconnection to Kafka on connection loss

---

## Monitoring and Health Checks

### Import Health Endpoint
- **Endpoint**: `/health/import`
- **Monitors**: GCS import system status
- **Checks**:
  - Import monitor running status
  - Recent import success/failure rates
  - Last successful import timestamp
  - Disk space availability

### Event Processing Metrics
- Total events published
- Total events consumed
- Processing latency
- Error rates by event type

---

## Best Practices

1. **Event Ordering**: Use patient_id as partition key to maintain order per patient
2. **Idempotency**: Design event handlers to be idempotent for replay safety
3. **Event Versioning**: Include version information in event payloads for future compatibility
4. **Monitoring**: Track event processing metrics and set up alerts for failures
5. **Testing**: Use test topics and consumer groups for development environments