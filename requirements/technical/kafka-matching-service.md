# Kafka in Matching Service
## Event-Driven Architecture Documentation

---

## Overview
The Matching Service uses Apache Kafka for asynchronous, event-driven communication between microservices. It acts as both an event producer (publishing events about anfragen and patient searches) and an event consumer (reacting to events from patient, therapist, and communication services).

---

## Kafka as Event Producer

The matching service publishes events to the **`matching-events`** topic to notify other services about matching activities and anfrage lifecycle changes.

### Published Events

#### 1. **`therapeutenanfrage.created`**
- **Trigger**: When a new anfrage (therapy request bundle) is created
- **Payload**:
  ```json
  {
    "anfrage_id": int,
    "therapist_id": int,
    "patient_ids": [int],
    "anfrage_size": int
  }
  ```
- **Purpose**: Notifies other services about new anfragen for tracking and analytics

#### 2. **`therapeutenanfrage.sent`**
- **Trigger**: When an anfrage is sent to a therapist via email or phone
- **Payload**:
  ```json
  {
    "anfrage_id": int,
    "communication_type": string ("email" | "phone_call"),
    "communication_id": int (optional)
  }
  ```
- **Purpose**: Tracks anfrage delivery and enables communication follow-up

#### 3. **`therapeutenanfrage.response_received`**
- **Trigger**: When a therapist responds to an anfrage
- **Payload**:
  ```json
  {
    "anfrage_id": int,
    "response_type": string ("vollstaendige_Annahme" | "teilweise_Annahme" | "vollstaendige_Ablehnung"),
    "accepted_count": int,
    "rejected_count": int,
    "no_response_count": int
  }
  ```
- **Purpose**: Enables tracking of therapist responses and success rates

#### 4. **`search.status_changed`**
- **Trigger**: When a patient search (Platzsuche) status changes
- **Payload**:
  ```json
  {
    "search_id": int,
    "patient_id": int,
    "old_status": string,
    "new_status": string ("aktiv" | "erfolgreich" | "pausiert" | "abgebrochen")
  }
  ```
- **Purpose**: Tracks patient search lifecycle and enables status-based workflows

#### 5. **`cooling.period_started`**
- **Trigger**: When a cooling period is initiated for a therapist
- **Payload**:
  ```json
  {
    "therapist_id": int,
    "next_contactable_date": string (ISO format),
    "reason": string ("response_received" | "manual")
  }
  ```
- **Purpose**: Prevents over-contacting therapists and maintains professional relationships

---

## Kafka as Event Consumer

The matching service consumes events from multiple topics to maintain data consistency and react to changes in other services.

### Consumed Events

#### From **`patient-events`** Topic:

##### 1. **`patient.deleted`**
- **Action**: Cancels active searches for deleted patients
- **Processing**:
  1. Identifies all active searches (Platzsuche) for the patient
  2. Updates search status to "abgebrochen" (cancelled)
  3. Adds cancellation note with reason
  4. Preserves historical anfrage data for audit trail
- **Expected Payload**:
  ```json
  {
    "patient_id": int
  }
  ```

##### 2. **`patient.updated`**
- **Action**: Currently logged for future implementation
- **Future Use**: Update matching criteria when patient preferences change
- **Expected Payload**:
  ```json
  {
    "patient_id": int,
    "updated_fields": [string]
  }
  ```

#### From **`therapist-events`** Topic:

##### 1. **`therapist.blocked`**
- **Action**: Handles therapist blocking scenarios
- **Processing**:
  1. Cancels all unsent anfragen for the blocked therapist
  2. Adds cancellation notes to affected anfragen
  3. Adds therapist to exclusion lists for patients with pending anfragen
  4. Preserves anfrage history for audit purposes
- **Expected Payload**:
  ```json
  {
    "therapist_id": int,
    "reason": string
  }
  ```

##### 2. **`therapist.unblocked`**
- **Action**: Currently logged for future implementation
- **Future Use**: Manual review required before removing from exclusion lists
- **Expected Payload**:
  ```json
  {
    "therapist_id": int
  }
  ```

#### From **`communication-events`** Topic:

##### 1. **`communication.email_sent`**
- **Action**: Currently processed without logging
- **Future Use**: Track email delivery confirmation for anfragen
- **Expected Payload**:
  ```json
  {
    "email_id": int,
    "email_data": {
      "therapist_id": int (optional),
      "patient_id": int (optional)
    }
  }
  ```

##### 2. **`communication.email_response_received`**
- **Action**: Currently logged for future implementation
- **Future Use**: Automated processing of email responses from therapists
- **Expected Payload**:
  ```json
  {
    "email_id": int,
    "response_data": object
  }
  ```

---

## Background Workers

### Follow-up Call Scheduler
- **Frequency**: Daily at 09:00
- **Function**: `schedule_follow_up_calls()`
- **Purpose**: Schedules phone calls for anfragen without responses
- **Process**:
  1. Identifies anfragen sent more than 7 days ago without responses
  2. Checks if phone call already scheduled
  3. Creates follow-up phone call via Communication Service API
  4. Updates anfrage with phone_call_id
  5. Publishes events for scheduled calls

### Configuration:
```python
# From shared/config.py
FOLLOW_UP_THRESHOLD_DAYS = 7  # Days before follow-up required
DEFAULT_PHONE_CALL_TIME = "10:00"  # Default call time
```

---

## Implementation Details

### Producer Implementation
```python
# Located in: matching_service/events/producers.py

from shared.kafka.robust_producer import RobustKafkaProducer

producer = RobustKafkaProducer(service_name="matching-service")
MATCHING_TOPIC = "matching-events"

# Example: Publishing anfrage created event
def publish_anfrage_created(
    anfrage_id: int,
    therapist_id: int,
    patient_ids: List[int],
    anfrage_size: int
) -> bool:
    return producer.send_event(
        topic=MATCHING_TOPIC,
        event_type="therapeutenanfrage.created",
        payload={
            "anfrage_id": anfrage_id,
            "therapist_id": therapist_id,
            "patient_ids": patient_ids,
            "anfrage_size": anfrage_size
        },
        key=str(anfrage_id)
    )
```

### Consumer Implementation
```python
# Located in: matching_service/events/consumers.py

from shared.kafka import EventSchema, KafkaConsumer
from db import get_db_context

def handle_patient_event(event: EventSchema) -> None:
    if event.event_type == "patient.deleted":
        patient_id = event.payload.get("patient_id")
        with get_db_context() as db:
            # Cancel active searches
            active_searches = db.query(Platzsuche).filter(
                Platzsuche.patient_id == patient_id,
                Platzsuche.status == SuchStatus.aktiv
            ).all()
            
            for search in active_searches:
                search.cancel_search("Patient deleted from system")
            db.commit()

def handle_therapist_event(event: EventSchema) -> None:
    if event.event_type == "therapist.blocked":
        therapist_id = event.payload.get("therapist_id")
        reason = event.payload.get("reason", "Therapist blocked")
        
        with get_db_context() as db:
            # Cancel unsent anfragen
            unsent_anfragen = db.query(Therapeutenanfrage).filter(
                Therapeutenanfrage.therapist_id == therapist_id,
                Therapeutenanfrage.gesendet_datum.is_(None)
            ).all()
            
            for anfrage in unsent_anfragen:
                anfrage.add_note(f"Cancelled: {reason}", author="System")
            db.commit()

# Start consumers
def start_consumers():
    # Patient events consumer
    patient_consumer = KafkaConsumer(
        topics=["patient-events"],
        group_id="matching-service-patient",
    )
    
    # Therapist events consumer
    therapist_consumer = KafkaConsumer(
        topics=["therapist-events"],
        group_id="matching-service-therapist",
    )
    
    # Communication events consumer
    communication_consumer = KafkaConsumer(
        topics=["communication-events"],
        group_id="matching-service-communication",
    )
    
    # Start processing in separate threads
    threading.Thread(
        target=patient_consumer.process_events,
        args=(handle_patient_event, ["patient.created", "patient.updated", "patient.deleted"]),
        daemon=True,
        name="patient-event-consumer"
    ).start()
```

---

## Event Flow Examples

### Example 1: Anfrage Creation and Sending
1. **User Action**: Admin creates anfrage for therapist
2. **Matching Service**:
   - Creates Therapeutenanfrage record
   - Publishes `therapeutenanfrage.created` event
   - Calls Communication Service API to create email
   - Publishes `therapeutenanfrage.sent` event
3. **Communication Service**:
   - Receives email creation request
   - Sends email
   - Publishes `communication.email_sent` event
4. **Matching Service**:
   - Consumes `communication.email_sent` event (for tracking)

### Example 2: Patient Deletion Cascade
1. **Patient Service**: Publishes `patient.deleted` event
2. **Matching Service**:
   - Consumes event
   - Cancels all active searches for patient
   - Publishes `search.status_changed` events
3. **Other Services**: React to status changes as needed

### Example 3: Follow-up Workflow
1. **Background Scheduler** (daily at 09:00):
   - Identifies anfragen older than 7 days without responses
2. **Matching Service**:
   - Calls Communication Service API to schedule phone calls
   - Updates anfragen with phone_call_ids
3. **Communication Service**:
   - Creates phone call records
   - Publishes `communication.call_scheduled` events

---

## Error Handling

### Producer Error Handling
- Uses `RobustKafkaProducer` with automatic retries
- Logs failures but doesn't block main application flow
- Events that fail to publish are logged for manual intervention

### Consumer Error Handling
- Each event handler wrapped in try-catch blocks
- Database transactions rolled back on errors
- Failed events logged but not retried (at-most-once delivery)
- Service continues running even if Kafka is unavailable

---

## Monitoring and Observability

### Key Metrics to Monitor
1. **Event Publishing**:
   - Total events published by type
   - Failed event publications
   - Event publishing latency

2. **Event Consumption**:
   - Events consumed by topic
   - Consumer lag
   - Processing errors by event type

3. **Business Metrics**:
   - Anfragen created/sent/responded per day
   - Average response time for anfragen
   - Follow-up calls scheduled vs completed

### Logging Strategy
- All event publications logged at INFO level
- Consumer processing logged at DEBUG level
- Errors logged at ERROR level with full stack traces
- Business events (anfrage lifecycle) logged at INFO level

---

## Configuration

### Environment Variables
```bash
# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_LOG_LEVEL=INFO

# Follow-up Configuration
FOLLOW_UP_THRESHOLD_DAYS=7
DEFAULT_PHONE_CALL_TIME=10:00

# Service Configuration
MATCHING_SERVICE_INTERNAL_PORT=8003
```

### Topics Configuration
```bash
# Topics used by Matching Service
matching-events       # Published to
patient-events       # Consumed from
therapist-events     # Consumed from
communication-events # Consumed from
```

---

## Future Enhancements

1. **Automated Email Response Processing**:
   - Parse therapist email responses
   - Automatically update anfrage statuses
   - Trigger follow-up workflows

2. **Real-time Matching**:
   - React to patient preference changes
   - Dynamically adjust anfrage compositions
   - Implement priority queuing

3. **Advanced Analytics Events**:
   - Publish detailed matching metrics
   - Track algorithm performance
   - Enable A/B testing of matching strategies

4. **Event Sourcing**:
   - Implement event replay capability
   - Build audit log from events
   - Enable time-travel debugging