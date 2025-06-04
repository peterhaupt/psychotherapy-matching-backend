"""Docker-based Kafka monitoring for all topics."""
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
    """Monitor all Kafka topics using Docker."""
    parser = ArgumentParser(description="Monitor All Kafka Topics")
    parser.add_argument(
        '--timeout',
        type=int,
        default=300,
        help='Time in seconds to listen for events (default: 300)'
    )
    parser.add_argument(
        '--from-beginning',
        action='store_true',
        help='Read messages from the beginning of the topics'
    )
    
    args = parser.parse_args()
    
    logger.info("Starting All Topics Kafka monitoring")
    logger.info(
        "This script will monitor ALL Kafka topics in the cluster"
    )
    
    # First, list all topics in the Kafka cluster
    list_cmd = (
        "docker-compose exec -T kafka "
        "kafka-topics --bootstrap-server kafka:9092 --list"
    )
    
    print("\n" + "*" * 80)
    print("1. First, run this command to see all available topics:")
    print(list_cmd)
    print("*" * 80 + "\n")
    
    # Build the docker-compose exec command to run kafka-console-consumer
    # for all topics
    from_beginning = "--from-beginning" if args.from_beginning else ""
    docker_cmd = (
        f"docker-compose exec -T kafka "
        f"kafka-console-consumer "
        f"--bootstrap-server kafka:9092 "
        f"--whitelist '.*' "  # Wildcard to match all topics
        f"{from_beginning} "
        f"--timeout-ms {args.timeout * 1000} "
        f"--property print.topic=true"  # Show which topic each message is from
    )
    
    logger.info(f"Waiting for events from all Kafka topics...")
    
    # Display the command for the user to execute
    print("\n" + "*" * 80)
    print("2. Then run this command to monitor ALL topics:")
    print(docker_cmd)
    print("*" * 80 + "\n")
    
    logger.info(
        "After running the command, use the various service APIs "
        "to create, update, or delete resources"
    )
    logger.info(
        "Events from ALL services will be displayed in the console. "
        "The topic name will be shown before each message."
    )
    
    # Example API calls to trigger events from different services
    print("\n" + "*" * 80)
    print("Example API calls to trigger events:")
    print("\n1. Patient Service:")
    print('curl -X POST http://localhost:8001/api/patients -H "Content-Type: application/json" -d \'{"vorname":"Max","nachname":"Mustermann"}\'')
    
    print("\n2. Therapist Service:")
    print('curl -X POST http://localhost:8002/api/therapists -H "Content-Type: application/json" -d \'{"vorname":"Jane","nachname":"Smith","titel":"Dr."}\'')
    
    print("\n3. Matching Service:")
    print('curl -X POST http://localhost:8003/api/placement-requests -H "Content-Type: application/json" -d \'{"patient_id":1,"therapist_id":1}\'')
    
    print("\n4. Communication Service (Emails):")
    print('curl -X POST http://localhost:8004/api/emails -H "Content-Type: application/json" -d \'{"therapist_id":1,"subject":"Test Email","body_html":"<p>Test Body</p>","body_text":"Test Body","recipient_email":"test@example.com","recipient_name":"Test User"}\'')
    
    print("\n5. Communication Service (Phone Calls):")
    print('curl -X POST http://localhost:8004/api/phone-calls -H "Content-Type: application/json" -d \'{"therapist_id":1}\'')
    print("*" * 80 + "\n")


if __name__ == "__main__":
    sys.exit(main())