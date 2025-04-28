# Kafka Integration Testing

## Summary
This document describes the approach for testing Kafka event integration in the Psychotherapy Matching Platform. It covers the challenges of testing Kafka in Docker environments, the implemented solutions, and recommended testing approaches.

## Testing Challenges

### Kafka Network Configuration
When running Kafka in Docker, several networking challenges arise:

1. **Advertised Listeners**: Kafka brokers advertise themselves using the `KAFKA_ADVERTISED_LISTENERS` configuration, which is set to `kafka:9092` in our Docker Compose. This hostname is:
   - Resolvable within the Docker network
   - Not resolvable from the host machine

2. **DNS Resolution**: When Python clients connect to Kafka:
   - Initial connection to `localhost:9092` succeeds
   - Subsequent metadata requests try to connect to `kafka:9092` (advertised listener)
   - Host machine can't resolve `kafka:9092`, causing connection failures

3. **Timeout Configuration**: Kafka clients have several timeout parameters that must be properly configured:
   - `connections_max_idle_ms` > `request_timeout_ms` > `fetch_max_wait_ms`
   - Incorrect settings cause client initialization failures

## Solution: Docker-Based Testing

After exploring different approaches, we implemented a Docker-based testing solution that leverages Kafka's built-in command-line tools.

### Approach Overview
The solution involves:
1. Running a script that generates a Docker command for Kafka monitoring
2. Executing that command to monitor Kafka events inside the Docker network
3. Triggering events through the application API

### Test Script Implementation

A `docker-kafka-test.py` script was created that:
- Takes parameters for topic name and timeout duration
- Generates a `docker-compose exec` command to run Kafka console consumer
- Provides instructions to help users monitor events

```python
def main():
    """Run the Kafka integration test using Docker."""
    parser = ArgumentParser(description="Test Kafka integration with Patient Service")
    parser.add_argument(
        '--topic',
        default='patient-events',
        help='Kafka topic to listen to (default: patient-events)'
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=60,
        help='Time in seconds to listen for events (default: 60)'
    )
    
    args = parser.parse_args()
    
    logger.info("Starting Kafka integration test")
    logger.info(
        "This script will use docker-compose to run the test inside "
        "the Docker network, where 'kafka' hostname is resolvable"
    )
    
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
    print("\n" + "*" * 80)
    print("To execute this test, run the following command in your terminal:")
    print(docker_cmd)
    print("*" * 80 + "\n")
```

## Testing Procedure

### Step 1: Start Docker Environment
Ensure all services are running:
```bash
docker-compose up -d
```

### Step 2: Run the Test Helper
```bash
python tests/integration/docker-kafka-test.py
```
This will output a Docker command to run.

### Step 3: Execute the Generated Command
Run the command displayed by the script in a terminal window.

### Step 4: Trigger Events
In another terminal, use curl or another tool to interact with the Patient Service API:
```bash
# Create a patient
curl -X POST http://localhost:8001/api/patients \
  -H "Content-Type: application/json" \
  -d '{"vorname":"Max","nachname":"Mustermann"}'

# Update a patient
curl -X PUT http://localhost:8001/api/patients/1 \
  -H "Content-Type: application/json" \
  -d '{"vorname":"Maximilian"}'

# Delete a patient
curl -X DELETE http://localhost:8001/api/patients/1
```

### Step 5: Observe Events
The terminal running the Kafka consumer command will display JSON event data for each action performed on the API.

## Alternative Approaches

### Host-Based Testing
A pure Python-based approach was attempted but faced challenges:

1. **Configuration Complexity**: Required complex modifications to deal with Kafka's advertised listeners
2. **DNS Issues**: Host machine couldn't resolve `kafka:9092` hostname
3. **Timeout Conflicts**: Difficult to configure all the timeout parameters correctly

The original script (`test_kafka_integration.py`) is preserved as a reference but is not recommended for testing.

### Kafka Listener Configuration
For production environments, it's recommended to configure Kafka with multiple listeners:
```
KAFKA_ADVERTISED_LISTENERS: INTERNAL://kafka:9092,EXTERNAL://localhost:9092
KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: INTERNAL:PLAINTEXT,EXTERNAL:PLAINTEXT
KAFKA_INTER_BROKER_LISTENER_NAME: INTERNAL
```

This would allow both container-to-container and host-to-container communication.

## Event Verification

The following events can be verified:

| API Action | Event Type | Description |
|------------|------------|-------------|
| POST /api/patients | patient.created | Published when a new patient is created |
| PUT /api/patients/<id> | patient.updated | Published when a patient is updated |
| DELETE /api/patients/<id> | patient.deleted | Published when a patient is deleted |

Each event follows the standard format:
```json
{
  "eventId": "uuid",
  "eventType": "patient.created",
  "version": "1.0",
  "timestamp": "ISO-8601",
  "producer": "patient-service",
  "payload": {
    "patient_id": 1,
    "patient_data": {
      "vorname": "Max",
      "nachname": "Mustermann",
      "email": "max@example.com",
      "status": "offen"
    }
  }
}
```

## Troubleshooting

### Common Issues
- **No events showing up**: Ensure the Patient Service is running and the API requests are successful
- **Connection refused**: Verify that Kafka is running with `docker-compose ps`
- **Topic not found**: Check if the topic exists with `docker-compose exec kafka kafka-topics --bootstrap-server kafka:9092 --list`

### Debugging
For more detailed debugging, you can examine the logs:
```bash
docker-compose logs -f patient-service  # Patient service logs
docker-compose logs -f kafka            # Kafka broker logs
```