# Kafka Configuration

## Summary
This document details the implementation of Kafka messaging infrastructure for the Psychotherapy Matching Platform. It covers Kafka and Zookeeper setup, topic configuration, shared utilities for event production and consumption, standardized event schemas, resilient messaging patterns, and the centralized configuration approach.

## Kafka and Zookeeper Infrastructure

### Docker Compose Configuration
The Kafka infrastructure consists of Zookeeper (for coordination) and Kafka brokers, configured in `docker-compose.yml`:
- Zookeeper with proper port and data directory setup
- Kafka with appropriate broker ID and listener configuration
- Volume mappings for data persistence
- Health check definitions

### Centralized Configuration
All Kafka settings are managed through `shared/config/settings.py`:

```python
from shared.config import get_config

config = get_config()

# Kafka configuration
bootstrap_servers = config.KAFKA_BOOTSTRAP_SERVERS  # Default: "kafka:9092"
zookeeper_connect = config.KAFKA_ZOOKEEPER_CONNECT  # Default: "zookeeper:2181"
```

### Environment Variables
Kafka settings in `.env`:
- `KAFKA_BOOTSTRAP_SERVERS`: Kafka broker addresses
- `KAFKA_ZOOKEEPER_CONNECT`: Zookeeper connection string

### Startup Dependencies with Healthchecks
Docker Compose healthchecks ensure proper service initialization:
1. **Zookeeper**: Checks its management port with a simple monitoring command
2. **Kafka**: Waits for Zookeeper to be healthy, then verifies it can list topics
3. **Services**: All microservices wait for Kafka to be healthy before starting

This approach, combined with the RobustKafkaProducer, provides two layers of protection:
- **Container-level**: Healthchecks ensure proper startup order
- **Application-level**: RobustKafkaProducer handles transient failures

## Kafka Topic Configuration

### Topic Initialization
A dedicated script initializes Kafka topics when the platform starts: `docker/kafka/create-topics.sh`

### Topics Created
The script creates the following topics with appropriate configurations:
- `patient-events`: Events related to patient operations
- `therapist-events`: Events related to therapist operations
- `matching-events`: Events related to matching/placement requests
- `communication-events`: Events related to emails and phone calls
- `geocoding-events`: Events related to geocoding operations
- `email-commands`: Commands for email operations
- `geocoding-requests`: Requests for geocoding calculations

Each topic is created with 3 partitions and replication factor of 1 (suitable for development).

## Shared Kafka Utilities

### Event Schema
A standardized event schema ensures consistent message format across all services. Implementation in `shared/kafka/schemas.py`:

```python
from shared.kafka import EventSchema

# Create an event
event = EventSchema(
    event_type="patient.created",
    payload={"patient_id": 123, "data": {...}},
    producer="patient-service"
)
```

Key fields in the standard event schema:
- `event_id`: Unique identifier for the event
- `event_type`: Type of event (e.g., "patient.created")
- `version`: Schema version for forward compatibility
- `timestamp`: When the event was created
- `producer`: Service that generated the event
- `payload`: Event-specific data

### Robust Kafka Producer
The resilient producer implementation in `shared/kafka/robust_producer.py` uses centralized configuration:

```python
from shared.kafka.robust_producer import RobustKafkaProducer

# Initialize with service name
producer = RobustKafkaProducer(service_name="my-service")

# Configuration is automatically loaded from shared.config
```

Key features:
- **Non-blocking initialization**: Services continue starting even when Kafka is unavailable
- **Connection retry**: Exponential backoff retry logic for connecting to Kafka
- **Message queuing**: Local storage of messages when Kafka is unavailable
- **Background processing**: Thread for sending queued messages when connection is restored
- **Error handling**: Proper handling of various error conditions

### Kafka Consumer
The consumer wrapper in `shared/kafka/consumer.py` also uses centralized configuration:

```python
from shared.kafka import KafkaConsumer

# Create consumer - configuration loaded automatically
consumer = KafkaConsumer(
    topics=["patient-events"],
    group_id="my-service"
)

# Process events
consumer.process_events(handler_function, event_types=["patient.created"])
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
- `communication.email_created`: An email has been created
- `communication.email_sent`: An email has been sent
- `communication.call_scheduled`: A phone call has been scheduled
- `communication.call_completed`: A phone call has been completed
- `geocoding.distance_result`: Distance calculation completed
- `geocoding.geocode_result`: Geocoding completed
- `geocoding.therapist_search_result`: Therapist search completed

### Command Events
Events that represent commands to be processed:
- `email.send`: Request to send an email
- `geocoding.calculate_distance`: Request to calculate distance between locations
- `geocoding.search_therapists`: Request to find therapists within distance
- `scraping.run`: Request to initiate web scraping

## Resilience Patterns

### Service Startup Independent of Kafka
Services can start and function even when Kafka is temporarily unavailable, thanks to the robust producer implementation that automatically uses configuration from `shared.config`.

### Message Queuing During Outages
Messages are queued locally when Kafka is unavailable and sent once the connection is restored.

### Automatic Reconnection
Services automatically attempt to reconnect to Kafka using an exponential backoff strategy.

### Consumer Error Handling
Consumers implement proper error handling for failed message processing without crashing the service.

## Configuration for Different Environments

### Development
```python
# Default configuration in shared/config/settings.py
KAFKA_BOOTSTRAP_SERVERS = "kafka:9092"
```

### Production
```python
# Override via environment variables
KAFKA_BOOTSTRAP_SERVERS = "kafka1:9092,kafka2:9092,kafka3:9092"
# Additional production settings can be added
```

### Testing
```python
# Mock Kafka for unit tests
# Or use embedded Kafka for integration tests
```

## Testing Kafka Integration

### Docker-Based Testing
Use the provided test scripts in `tests/integration/`:

```bash
# Monitor all topics
python tests/integration/all_topics_monitor.py

# This generates Docker commands to monitor Kafka events
```

### Verifying Event Flow
1. Start monitoring Kafka topics
2. Perform API operations (create/update/delete resources)
3. Observe events flowing through Kafka
4. Verify event schema and content

## Best Practices

1. **Use Centralized Configuration**: Always rely on `shared.config` for Kafka settings
2. **Use RobustKafkaProducer**: Ensures resilient message delivery
3. **Follow Event Schema**: Use the standardized EventSchema for all events
4. **Handle Consumer Errors**: Implement proper error handling in consumers
5. **Test Event Flows**: Verify events are published and consumed correctly
6. **Monitor Topics**: Regularly check topic health and message flow
7. **Environment-Specific Settings**: Use environment variables for different deployments

## Troubleshooting

### Connection Issues
1. Check Kafka is running: `docker-compose ps kafka`
2. Verify configuration: Ensure `KAFKA_BOOTSTRAP_SERVERS` is correct
3. Check logs: `docker-compose logs kafka`
4. Test connection: Use kafka-topics command to list topics

### Message Not Delivered
1. Check producer logs for queued messages
2. Verify topic exists: `docker-compose exec kafka kafka-topics --list --bootstrap-server kafka:9092`
3. Check consumer group lag
4. Verify event type matches consumer filter

### Configuration Problems
1. Verify `.env` file has correct values
2. Check if configuration is loaded: Print `config.KAFKA_BOOTSTRAP_SERVERS`
3. Ensure shared package is in Python path