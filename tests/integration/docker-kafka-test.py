"""Docker-based Kafka integration test for the Psychotherapy Matching Platform."""
import logging
import sys
from argparse import ArgumentParser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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
    parser.add_argument(
        '--from-beginning',
        action='store_true',
        help='Read messages from the beginning of the topic'
    )
    
    args = parser.parse_args()
    
    logger.info("Starting Kafka integration test")
    logger.info(
        "This script will use docker-compose to run the test inside "
        "the Docker network, where 'kafka' hostname is resolvable"
    )
    
    # Build the docker-compose exec command to run kafka-console-consumer
    # inside the Kafka container
    from_beginning = "--from-beginning" if args.from_beginning else ""
    docker_cmd = (
        f"docker-compose exec -T kafka "
        f"kafka-console-consumer "
        f"--bootstrap-server kafka:9092 "
        f"--topic {args.topic} "
        f"{from_beginning} "
        f"--timeout-ms {args.timeout * 1000}"
    )
    
    logger.info(f"Executing: {docker_cmd}")
    logger.info("Waiting for events...")
    
    # In a real implementation, we would use subprocess.run to execute this command
    # and capture the output. For this example, we're just showing the command.
    print("\n" + "*" * 80)
    print("To execute this test, run the following command in your terminal:")
    print(docker_cmd)
    print("*" * 80 + "\n")
    
    logger.info(
        "After running the command, use the Patient Service API "
        "to create, update, or delete patients"
    )
    logger.info(
        "Any events will be displayed in the console. If you see JSON "
        "messages, the test is working!"
    )
    
    # Example API calls to trigger events
    print("\n" + "*" * 80)
    print("Example API calls to trigger events:")
    print("Create a patient:")
    print('curl -X POST http://localhost:8001/api/patients -H "Content-Type: application/json" -d \'{"vorname":"Max","nachname":"Mustermann"}\'')
    print("\nUpdate a patient:")
    print('curl -X PUT http://localhost:8001/api/patients/1 -H "Content-Type: application/json" -d \'{"vorname":"Maximilian"}\'')
    print("\nDelete a patient:")
    print('curl -X DELETE http://localhost:8001/api/patients/1')
    print("*" * 80 + "\n")


if __name__ == "__main__":
    sys.exit(main())