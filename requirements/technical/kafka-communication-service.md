# Kafka in Communication Service
## Event-Driven Architecture Documentation

---

## Overview
The Communication Service uses Apache Kafka for asynchronous, event-driven communication between microservices. It acts as both an event producer (publishing events when communication actions occur) and an event consumer (reacting to communication requests from other services).

---

## Kafka as Event Producer

The communication service publishes events to the **`communication-events`** topic to notify other services about communication activities.

### Published Events

#### 1. **`email.sent`**
- **Trigger**: When an email is successfully sent
- **Payload**:
  ```json
  {
    "email_id": int,
    "email_data": {
      "therapist_id": int (optional),
      "patient_id": int (optional),
      "betreff": string,
      "recipient_type": string,
      "status": string
    },
    "communication_type": "email"
  }
  ```
- **Purpose**: Allows other services to track email delivery and update communication history

#### 2. **`email.response_received`**
- **Trigger**: When a response to an email is received
- **Payload**:
  ```json
  {
    "email_id": int,
    "email_data": {...},
    "communication_type": "email",
    "patient_id": int (optional),
    "therapist_id": int (optional)
  }
  ```
- **Purpose**: Tracks engagement and enables follow-up actions

#### 3. **`phone_call.completed`**
- **Trigger**: When a phone call status changes to "abgeschlossen" (completed)
- **Payload**:
  ```json
  {
    "call_id": int,
    "call_data": {
      "therapist_id": int (optional),
      "patient_id": int (optional),
      "therapeutenanfrage_id": int (optional),
      "recipient_type": string,
      "status": string,
      "ergebnis": string
    },
    "communication_type": "phone_call",
    "outcome": string (optional)
  }
  ```
- **Purpose**: Enables tracking of call outcomes and triggering follow-up workflows

#### 4. **`communication.email_created`**
- **Trigger**: When a new email is created in the system
- **Payload**:
  ```json
  {
    "email_id": int,
    "email_data": {...}
  }
  ```
- **Purpose**: Notifies other services about new emails for processing

#### 5. **`communication.call_scheduled`**
- **Trigger**: When a phone call is scheduled
- **Payload**:
  ```json
  {
    "call_id": int,
    "call_data": {
      "therapist_id": int (optional),
      "patient_id": int (optional),
      "therapeutenanfrage_id": int (optional),
      "recipient_type": string,
      "scheduled_date": string (ISO format),
      "scheduled_time": string (ISO format)
    }
  }
  ```
- **Purpose**: Allows other services to track scheduled communications

---

## Kafka as Event Consumer

The communication service consumes events from the **`communication-events`** topic to handle communication requests from other services.

### Consumed Events

#### 1. **`communication.send_email`**
- **Action**: Triggers immediate email sending
- **Processing**:
  1. Retrieves email from database using provided `email_id`
  2. Checks if email status is "In_Warteschlange" (queued)
  3. Sends email via SMTP
  4. Updates email status to "Gesendet" (sent) or "Fehlgeschlagen" (failed)
  5. Records timestamp of sending
- **Expected Payload**:
  ```json
  {
    "email_id": int
  }
  ```

#### 2. **`communication.schedule_call`**
- **Action**: Logs phone call scheduling requests
- **Processing**:
  1. Extracts `therapist_id` or `patient_id` from event
  2. Logs the scheduling request for tracking
  3. Note: Actual scheduling should be done via direct API call
- **Expected Payload**:
  ```json
  {
    "therapist_id": int (optional),
    "patient_id": int (optional)
  }
  ```

---

## Background Workers

### Email Queue Processor
- **Frequency**: Every 60 seconds
- **Function**: `process_email_queue()`
- **Purpose**: Processes queued emails independently of Kafka events
- **Process**:
  1. Queries database for emails with status "In_Warteschlange"
  2. Sends up to 10 emails per batch
  3. Updates status and timestamps
  4. Publishes `email.sent` events for successful sends

---

## Implementation Details

### Producer Implementation
```python
# Located in: communication_service/events/producers.py

from shared.kafka.robust_producer import RobustKafkaProducer

producer = RobustKafkaProducer(service_name="communication-service")
COMMUNICATION_TOPIC = "communication-events"

# Example: Publishing email sent event
def publish_email_sent(email_id: int, email_data: Dict[str, Any]) -> bool:
    payload = {
        "email_id": email_id,
        "email_data": email_data,
        "communication_type": "email"
    }
    
    return producer.send_event(
        topic=COMMUNICATION_TOPIC,
        event_type="email.sent",
        payload=payload,
        key=str(email_id)
    )
```

### Consumer Implementation
```python
# Located in: communication_service/events/consumers.py

from shared.kafka import KafkaConsumer

def handle_matching_event(event: EventSchema) -> None:
    if event.event_type == "communication.send_email":
        # Process email sending
        email_id = event.payload.get("email_id")
        # ... send email logic
    
    elif event.event_type == "communication.schedule_call":
        # Log call scheduling request
        # ... logging logic

# Start consumer
matching_consumer = KafkaConsumer(
    topics=["communication-events"],
    group_id="communication-service",
)
```

