# Kafka in Therapist Service
## Event-Driven Architecture Documentation

---

## Overview
The Therapist Service uses Apache Kafka for asynchronous, event-driven communication between microservices. It primarily acts as an event producer, publishing events when therapist-related actions occur (creation, updates, status changes). The service also has consumer capabilities for receiving events from other services, though these are currently dormant pending future integration needs.

---

## Kafka as Event Producer

The therapist service publishes events to the **`therapist-events`** topic to notify other services about therapist-related activities.

### Published Events

#### 1. **`therapist.created`**
- **Trigger**: When a new therapist is created (via API or import)
- **Payload**:
  ```json
  {
    "therapist_id": int,
    "therapist_data": {
      "id": int,
      "anrede": string,
      "geschlecht": string,
      "titel": string,
      "vorname": string,
      "nachname": string,
      "strasse": string,
      "plz": string,
      "ort": string,
      "telefon": string,
      "email": string,
      "kassensitz": boolean,
      "psychotherapieverfahren": string,
      "potenziell_verfuegbar": boolean,
      "status": string
    }
  }
  ```
- **Purpose**: Allows other services (especially matching service) to track new therapists and update their records

#### 2. **`therapist.updated`**
- **Trigger**: When therapist information is modified
- **Payload**:
  ```json
  {
    "therapist_id": int,
    "therapist_data": {
      // Complete updated therapist data structure
    }
  }
  ```
- **Purpose**: Synchronizes therapist data changes across all services

#### 3. **`therapist.blocked`**
- **Trigger**: When a therapist status changes to "gesperrt" (blocked)
- **Payload**:
  ```json
  {
    "therapist_id": int,
    "therapist_data": {...},
    "reason": string (optional)
  }
  ```
- **Purpose**: Notifies services to exclude blocked therapists from matching and communications

#### 4. **`therapist.unblocked`**
- **Trigger**: When a therapist status changes from "gesperrt" to "aktiv"
- **Payload**:
  ```json
  {
    "therapist_id": int,
    "therapist_data": {...}
  }
  ```
- **Purpose**: Notifies services that a therapist is available again for matching

---

## Kafka as Event Consumer (Future Ready)

The therapist service has infrastructure to consume events from the **`patient-events`** topic, though this functionality is currently not active.

### Consumable Events (When Activated)

#### 1. **`patient.created`**
- **Action**: Could trigger therapist matching suggestions
- **Processing**: Infrastructure exists but implementation pending
- **Expected Payload**:
  ```json
  {
    "patient_id": int,
    "patient_data": {...}
  }
  ```

#### 2. **`patient.updated`**
- **Action**: Could update therapist-patient relationships
- **Processing**: Infrastructure exists but implementation pending

---

## Background Workers

### Therapist Import Monitor
- **Frequency**: Every 24 hours (configurable via `THERAPIST_IMPORT_CHECK_INTERVAL_SECONDS`)
- **Function**: `start_therapist_import_monitor()`
- **Purpose**: Automatically imports therapists from scraped JSON files
- **Process**:
  1. Scans local directory for new therapist JSON files
  2. Processes latest file for each ZIP code
  3. Creates or updates therapist records
  4. Publishes appropriate Kafka events for each action
  5. Sends error notifications if imports fail

---

## Implementation Details

### Producer Implementation
```python
# Located in: therapist_service/events/producers.py

from shared.kafka.robust_producer import RobustKafkaProducer

producer = RobustKafkaProducer(service_name="therapist-service")
THERAPIST_TOPIC = "therapist-events"

# Example: Publishing therapist created event
def publish_therapist_created(therapist_id: int, therapist_data: Dict[str, Any]) -> bool:
    return producer.send_event(
        topic=THERAPIST_TOPIC,
        event_type="therapist.created",
        payload={
            "therapist_id": therapist_id,
            "therapist_data": therapist_data
        },
        key=str(therapist_id)
    )
```

### Consumer Implementation (Infrastructure Ready)
```python
# Located in: therapist_service/events/consumers.py

from shared.kafka import EventSchema

def handle_patient_event(event: EventSchema) -> None:
    if event.event_type == "patient.created":
        patient_id = event.payload.get("patient_id")
        # Future implementation for patient-triggered actions
        logger.info(f"Patient {patient_id} has been created")

# Consumer start function ready for activation
def start_consumers():
    # Currently inactive, ready for future activation
    # patient_consumer = KafkaConsumer(
    #     topics=["patient-events"],
    #     group_id="therapist-service",
    # )
    logger.info("Kafka consumers initialized")
```

---

## Event Flow Patterns

### 1. Therapist Creation Flow
```
User/Import → Therapist Service → Database
                ↓
         Kafka Event (therapist.created)
                ↓
         Matching Service (updates available therapists)
```

### 2. Therapist Status Change Flow
```
Admin Action → Therapist Service → Database Update
                    ↓
            Kafka Event (therapist.blocked/unblocked)
                    ↓
            ┌───────┴───────┐
     Matching Service   Communication Service
     (updates lists)    (stops/resumes outreach)
```

### 3. Import Process Flow
```
Import Monitor (24h) → JSON Files → Therapist Importer
                            ↓
                    Database Operations
                            ↓
                    Kafka Events (create/update)
                            ↓
                    Other Services Updated
```

---

## Configuration

### Environment Variables
```bash
# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_LOG_LEVEL=INFO

# Import Configuration
THERAPIST_IMPORT_FOLDER_PATH=/scraping_data
THERAPIST_IMPORT_CHECK_INTERVAL_SECONDS=86400  # 24 hours
THERAPIST_IMPORT_ENABLED=true
```

### Topics Configuration
- **Primary Topic**: `therapist-events`
- **Partitions**: 3
- **Replication Factor**: 1 (development), should be increased for production

---

## Error Handling

### Producer Error Handling
- Uses `RobustKafkaProducer` with automatic retries
- Logs failures but doesn't block API operations
- Events that fail to send are logged for manual investigation

### Import Error Handling
- Collects all import errors during batch processing
- Sends summary email notification with error details
- Continues processing despite individual failures
- Maintains import status tracking via `ImportStatus` class

---

## Monitoring and Health Checks

### Import Health Check Endpoint
- **Endpoint**: `/health/import`
- **Monitors**:
  - Import monitor running status
  - Last successful import time
  - Files processed today
  - Failure rates
  - Recent errors

### Import Status Endpoint
- **Endpoint**: `/api/therapists/import-status`
- **Provides**:
  - Current import statistics
  - Recent import history
  - Next scheduled import time
  - Error tracking

---

## Best Practices

### 1. Event Publishing
- Always publish events AFTER successful database commits
- Include complete therapist data in events for service autonomy
- Use therapist ID as Kafka message key for ordering

### 2. Import Processing
- Process only the latest file per ZIP code to avoid duplicates
- Never overwrite manually managed fields during imports
- Preserve existing email addresses when import has empty values

### 3. Error Recovery
- Import process continues despite individual failures
- Failed imports are reported via email notifications
- System maintains detailed error logs for debugging

---

## Integration Points

### With Matching Service
- Receives therapist status updates for availability management
- Updates therapist pool for patient matching

### With Communication Service
- Can trigger emails/calls via direct API calls
- Updates last contact dates when communications occur

### With Scraping Service
- Reads JSON files from shared volume
- Processes therapist data from web scraping results

---

## Future Enhancements

### Planned Consumer Features
1. **Patient Event Processing**
   - Auto-suggest therapists for new patients
   - Update therapist workload based on patient assignments

2. **Matching Event Reactions**
   - Update therapist availability after successful matches
   - Track therapist response rates to inquiries

3. **Communication Event Integration**
   - Update contact history from communication events
   - Trigger follow-ups based on communication patterns

### Scalability Considerations
- Consumer group infrastructure ready for horizontal scaling
- Partition strategy supports parallel processing
- Event replay capability for disaster recovery