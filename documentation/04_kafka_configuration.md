# Kafka Configuration

## Summary
This document details the implementation of Kafka messaging infrastructure for the Psychotherapy Matching Platform. It covers Kafka and Zookeeper setup, topic configuration, shared utilities for event production and consumption, standardized event schemas, and resilient messaging patterns to enable asynchronous communication between microservices.

## Kafka and Zookeeper Infrastructure

### Docker Compose Configuration
The Kafka infrastructure consists of Zookeeper (for coordination) and Kafka brokers, configured in `docker-compose.yml`. The configuration includes:
- Zookeeper with proper port and data directory setup
- Kafka with appropriate broker ID and listener configuration
- Volume mappings for data persistence
- Health check definitions

### Startup Dependencies with Healthchecks
To ensure proper service initialization, Docker Compose healthchecks are used:
1. **Zookeeper**: Checks its management port with a simple monitoring command
2. **Kafka**: Waits for Zookeeper to be healthy, then verifies it can list topics
3. **Services**: All microservices wait for Kafka to be healthy before starting

This approach, combined with the RobustKafkaProducer, provides two layers of protection:
- **Container-level**: Healthchecks ensure proper startup order
- **Application-level**: RobustKafkaProducer handles transient failures

## Kafka Topic Configuration

### Topic Initialization
A dedicated service is added to initialize Kafka topics when the platform starts. This is implemented in `docker-compose.yml` with the "kafka-setup" service.

### Topic Creation Script
The `docker/kafka/create-topics.sh` script creates the required Kafka topics with appropriate partitioning and replication configurations.

## Shared Kafka Utilities

### Event Schema
A standardized event schema ensures consistent message format across all services. Implementation can be found in `shared/kafka/schemas.py`.

Key fields in the standard event schema:
- `event_id`: Unique identifier for the event
- `event_type`: Type of event (e.g., "patient.created")
- `version`: Schema version for forward compatibility
- `timestamp`: When the event was created
- `producer`: Service that generated the event
- `payload`: Event-specific data

### Robust Kafka Producer
A resilient wrapper around the Kafka producer with advanced failure handling is implemented in `shared/kafka/robust_producer.py`.

Key features:
- **Non-blocking initialization**: Services continue starting even when Kafka is unavailable
- **Connection retry**: Exponential backoff retry logic for connecting to Kafka
- **Message queuing**: Local storage of messages when Kafka is unavailable
- **Background processing**: Thread for sending queued messages when connection is restored
- **Error handling**: Proper handling of various error conditions

### Kafka Consumer
A wrapper around the Kafka consumer to standardize event processing is available in `shared/kafka/consumer.py`.

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

## Resilience Patterns

### Service Startup Independent of Kafka
Services can start and function even when Kafka is temporarily unavailable, thanks to the robust producer implementation.

### Message Queuing During Outages
Messages are queued locally when Kafka is unavailable and sent once the connection is restored.

### Automatic Reconnection
Services automatically attempt to reconnect to Kafka using an exponential backoff strategy.

### Consumer Error Handling
Consumers implement proper error handling for failed message processing without crashing the service.