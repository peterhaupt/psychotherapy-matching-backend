# Kafka Configuration

## Summary
This document details the implementation of Kafka messaging infrastructure for the Psychotherapy Matching Platform. It covers Kafka and Zookeeper setup, topic configuration, shared utilities for event production and consumption, standardized event schemas, and resilient messaging patterns to enable asynchronous communication between microservices.

## Kafka and Zookeeper Infrastructure

### Docker Compose Configuration

The Kafka infrastructure consists of Zookeeper (for coordination) and Kafka brokers, configured in `docker-compose.yml`:

```yaml
zookeeper:
  image: confluentinc/cp-zookeeper:latest
  environment:
    ZOOKEEPER_CLIENT_PORT: 2181
    ZOOKEEPER_TICK_TIME: 2000
  ports:
    - "2181:2181"
  volumes:
    - zookeeper-data:/var/lib/zookeeper/data
    - zookeeper-logs:/var/lib/zookeeper/log
  restart: unless-stopped
  healthcheck:
    test: ["CMD-SHELL", "echo mntr | nc localhost 2181"]
    interval: 5s
    timeout: 5s
    retries: 3
    start_period: 10s

kafka:
  image: confluentinc/cp-kafka:latest
  depends_on:
    zookeeper:
      condition: service_healthy
  ports:
    - "9092:9092"
  environment:
    KAFKA_BROKER_ID: 1
    KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
    KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
    KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
    KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
    KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS: 0
  volumes:
    - kafka-data:/var/lib/kafka/data
  restart: unless-stopped
  healthcheck:
    test: ["CMD-SHELL", "kafka-topics --bootstrap-server kafka:9092 --list || exit 1"]
    interval: 10s
    timeout: 20s
    retries: 5
    start_period: 30s
```

Additional volumes are defined:
```yaml
volumes:
  zookeeper-data:
  zookeeper-logs:
  kafka-data:
```

### Startup Dependencies with Healthchecks

To ensure proper service initialization, we use Docker Compose healthchecks:

1. **Zookeeper**: Checks its management port with a simple monitoring command
2. **Kafka**: Waits for Zookeeper to be healthy, then verifies it can list topics
3. **Services**: All microservices wait for Kafka to be healthy before starting

This approach, combined with the RobustKafkaProducer, provides two layers of protection:
- **Container-level**: Healthchecks ensure proper startup order
- **Application-level**: RobustKafkaProducer handles transient failures

## Kafka Topic Configuration

### Topic Initialization

A dedicated service is added to initialize Kafka topics when the platform starts:

```yaml
kafka-setup:
  image: confluentinc/cp-kafka:latest
  depends_on:
    kafka:
      condition: service_healthy
  volumes:
    - ./docker/kafka:/scripts
  command: ["bash", "-c", "/scripts/create-topics.sh"]
  restart: "no"
```

### Topic Creation Script

The `docker/kafka/create-topics.sh` script creates the required Kafka topics:

```bash
#!/bin/bash
# Script to create required Kafka topics

# Wait for Kafka to be ready
echo "Waiting for Kafka to be ready..."
kafka-topics --bootstrap-server kafka:9092 --list
until [ $? -eq 0 ]; do
  sleep 5
  kafka-topics --bootstrap-server kafka:9092 --list
done

# Create topics with appropriate configurations
echo "Creating Kafka topics..."

# Event topics
kafka-topics --bootstrap-server kafka:9092 --create --if-not-exists \
  --topic patient-events --partitions 3 --replication-factor 1

kafka-topics --bootstrap-server kafka:9092 --create --if-not-exists \
  --topic therapist-events --partitions 3 --replication-factor 1

kafka-topics --bootstrap-server kafka:9092 --create --if-not-exists \
  --topic matching-events --partitions 3 --replication-factor 1

kafka-topics --bootstrap-server kafka:9092 --create --if-not-exists \
  --topic communication-events --partitions 3 --replication-factor 1

# Command topics
kafka-topics --bootstrap-server kafka:9092 --create --if-not-exists \
  --topic email-commands --partitions 3 --replication-factor 1

kafka-topics --bootstrap-server kafka:9092 --create --if-not-exists \
  --topic geocoding-requests --partitions 3 --replication-factor 1

echo "Kafka topics created:"
kafka-topics --bootstrap-server kafka:9092 --list
```

## Shared Kafka Utilities

A set of shared utilities is implemented to standardize Kafka interaction across microservices.

### Event Schema (`shared/kafka/schemas.py`)

A standardized event schema ensures consistent message format:

```python
class EventSchema:
    """Standard event schema for Kafka messages."""

    def __init__(
        self,
        event_type: str,
        payload: Dict[str, Any],
        producer: str,
        event_id: Optional[str] = None,
        version: str = "1.0"
    ):
        """Initialize a new event schema."""
        self.event_id = event_id or str(uuid.uuid4())
        self.event_type = event_type
        self.version = version
        self.timestamp = datetime.utcnow().isoformat()
        self.producer = producer
        self.payload = payload

    def to_dict(self) -> Dict[str, Any]:
        """Convert the event to a dictionary format."""
        return {
            "eventId": self.event_id,
            "eventType": self.event_type,
            "version": self.version,
            "timestamp": self.timestamp,
            "producer": self.producer,
            "payload": self.payload
        }

    def to_json(self) -> str:
        """Serialize the event to JSON."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> 'EventSchema':
        """Deserialize JSON to an EventSchema object."""
        data = json.loads(json_str)
        event = cls(
            event_type=data["eventType"],
            payload=data["payload"],
            producer=data["producer"],
            event_id=data["eventId"],
            version=data["version"]
        )
        event.timestamp = data["timestamp"]
        return event
```

### Robust Kafka Producer (`shared/kafka/robust_producer.py`)

A resilient wrapper around the Kafka producer with advanced failure handling:

```python
class RobustKafkaProducer:
    """Wrapper for Kafka producer with resilience capabilities."""

    def __init__(
        self,
        bootstrap_servers: str = "kafka:9092",
        service_name: str = "unknown-service"
    ):
        """Initialize the robust Kafka producer."""
        self.bootstrap_servers = bootstrap_servers
        self.service_name = service_name
        self.logger = logging.getLogger(__name__)
        self.producer = None
        self.connected = False
        self.message_queue = []
        self.queue_lock = Lock()
        
        # Try to connect without blocking startup
        self._connect()
        
        # Start background thread for reconnection and queue processing
        self.queue_processor = Thread(
            target=self._process_queue,
            daemon=True
        )
        self.queue_processor.start()
```

Key features of the robust producer:
- **Non-blocking initialization**: Services continue starting even when Kafka is unavailable
- **Connection retry**: Exponential backoff retry logic for connecting to Kafka
- **Message queuing**: Local storage of messages when Kafka is unavailable
- **Background processing**: Thread for sending queued messages when connection is restored
- **Error handling**: Proper handling of various error conditions

Implementation details:
1. **Connection management**: Handles connection attempts with retry logic
2. **Message queueing**: Stores events in memory when Kafka is unavailable
3. **Background processing**: Dedicated thread for reconnection and sending queued messages
4. **Standard event schema**: Maintains the same schema for all messages

### Kafka Consumer (`shared/kafka/consumer.py`)

A wrapper around the Kafka consumer to standardize event processing:

```python
class KafkaConsumer:
    """Wrapper for Kafka consumer with standardized event handling."""

    def __init__(
        self,
        topics: List[str],
        group_id: str,
        bootstrap_servers: str = "kafka:9092",
        auto_offset_reset: str = "earliest"
    ):
        """Initialize the Kafka consumer."""
        self.topics = topics
        self.group_id = group_id
        self.logger = logging.getLogger(__name__)

        try:
            self.consumer = BaseKafkaConsumer(
                *topics,
                bootstrap_servers=bootstrap_servers,
                group_id=group_id,
                auto_offset_reset=auto_offset_reset,
                value_deserializer=lambda v: json.loads(v.decode('utf-8'))
            )
        except KafkaError as e:
            self.logger.error(f"Failed to create Kafka consumer: {str(e)}")
            raise

    def process_events(
        self,
        handler: Callable[[EventSchema], None],
        event_types: Optional[List[str]] = None,
        timeout_ms: int = 1000
    ):
        """Process events from subscribed topics."""
        try:
            for message in self.consumer:
                try:
                    # Extract value and convert to EventSchema
                    event_data = message.value
                    
                    # Skip if event_types is specified and type not included
                    if (event_types and 
                            "eventType" in event_data and
                            event_data["eventType"] not in event_types):
                        continue
                    
                    event = EventSchema(
                        event_type=event_data["eventType"],
                        payload=event_data["payload"],
                        producer=event_data["producer"],
                        event_id=event_data["eventId"],
                        version=event_data["version"]
                    )
                    
                    # Process the event
                    handler(event)
                    
                    # Commit offset after successful processing
                    self.consumer.commit()
                    
                except Exception as e:
                    self.logger.error(
                        f"Error processing event: {str(e)}",
                        extra={"topic": message.topic, "partition": message.partition}
                    )
        except KafkaError as e:
            self.logger.error(f"Kafka error during consumption: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error during event processing: {str(e)}")

    def close(self):
        """Close the Kafka consumer."""
        self.consumer.close()
```

## Event Types

### Domain Events
Events that represent changes to domain entities:
- `patient.created`: A new patient has been created
- `patient.updated`: A patient's data has been changed
- `patient.deleted`: A patient has been removed
- `therapist.created`: A new therapist has been added
- `therapist.updated`: A therapist's data has been changed
- `therapist.blocked`: A therapist has been blocked
- `therapist.unblocked`: A therapist has been unblocked
- `match.created`: A new potential match has been identified
- `match.status_changed`: The status of a match has changed
- `communication.email_sent`: An email has been sent
- `communication.call_scheduled`: A phone call has been scheduled

### Command Events
Events that represent commands to be processed:
- `email.send`: Request to send an email
- `geocoding.calculate_distance`: Request to calculate distance between locations
- `scraping.run`: Request to initiate web scraping

## Usage Examples

### Producing Events

```python
# Initialize a robust producer in a service
producer = RobustKafkaProducer(service_name="patient-service")

# Send an event when a patient is created
def create_patient(data):
    # Create patient in database
    patient = Patient(**data)
    db.add(patient)
    db.commit()
    
    # Publish event
    producer.send_event(
        topic="patient-events",
        event_type="patient.created",
        payload={
            "patient_id": patient.id,
            "vorname": patient.vorname,
            "nachname": patient.nachname,
            # Other relevant data
        }
    )
    
    return patient
```

### Consuming Events

```python
# Initialize a consumer in a service
consumer = KafkaConsumer(
    topics=["patient-events"],
    group_id="matching-service"
)

# Define an event handler
def handle_patient_event(event: EventSchema):
    if event.event_type == "patient.created":
        # Process the new patient event
        patient_id = event.payload.get("patient_id")
        process_new_patient(patient_id)
    elif event.event_type == "patient.updated":
        # Process the patient update
        update_matching_data(event.payload)

# Start processing events in a separate thread
import threading
thread = threading.Thread(
    target=consumer.process_events,
    args=(handle_patient_event, ["patient.created", "patient.updated"]),
    daemon=True
)
thread.start()
```

## Resilience Patterns

The platform implements several resilience patterns for Kafka messaging:

### Service Startup Independent of Kafka

Services can start and function even when Kafka is temporarily unavailable:

```python
# In service initialization
try:
    # Robust producer handles connection failures gracefully
    producer = RobustKafkaProducer(service_name="service-name")
    logger.info("Connected to Kafka")
except Exception as e:
    logger.error(f"Error initializing Kafka producer: {str(e)}")
    # Service continues to operate, with events being queued
```

### Message Queuing During Outages

Messages are queued locally when Kafka is unavailable:

```python
# Producer handles queueing automatically
producer.send_event(
    topic="topic-name",
    event_type="event.type",
    payload={"key": "value"}
)  # Will be queued if Kafka is down
```

### Automatic Reconnection

Services automatically attempt to reconnect to Kafka:

```python
# RobustKafkaProducer implements reconnection logic
def _process_queue(self):
    """Background thread to process message queue."""
    retry_delay = 1  # Start with 1 second
    
    while True:
        # Try to reconnect if disconnected
        if not self.connected:
            if self._connect():
                retry_delay = 1  # Reset on success
            else:
                # Exponential backoff
                retry_delay = min(retry_delay * 2, 30)
                time.sleep(retry_delay)
        
        # Rest of queue processing
        # ...
```

### Consumer Error Handling

Consumers implement proper error handling for failed message processing:

```python
try:
    # Process the event
    handler(event)
    
    # Commit offset after successful processing
    self.consumer.commit()
except Exception as e:
    self.logger.error(f"Error processing event: {str(e)}")
    # Error is contained, processing continues with next message
```

## Integration Testing

The platform includes Docker-based testing tools for Kafka integration:

```python
# docker-kafka-test.py
def main():
    """Run the Kafka integration test using Docker."""
    parser = ArgumentParser(description="Test Kafka integration")
    parser.add_argument(
        '--topic',
        default='patient-events',
        help='Kafka topic to listen to (default: patient-events)'
    )
    
    args = parser.parse_args()
    
    # Build the docker-compose exec command
    docker_cmd = (
        f"docker-compose exec -T kafka "
        f"kafka-console-consumer "
        f"--bootstrap-server kafka:9092 "
        f"--topic {args.topic} "
        f"--from-beginning "
        f"--timeout-ms {args.timeout * 1000}"
    )
    
    # Display the command for the user to execute
    print(docker_cmd)
```

This approach resolves network issues with direct Kafka connections from the host machine by running the consumer inside the Docker network.