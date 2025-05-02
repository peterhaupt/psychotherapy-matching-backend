"""Test script for the matching algorithm."""
import sys
import os
import logging
from argparse import ArgumentParser

# Add the project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from matching_service.algorithms.matcher import (
    find_matching_therapists,
    create_placement_requests
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Run the matching algorithm test."""
    parser = ArgumentParser(description="Test the matching algorithm")
    parser.add_argument(
        '--patient',
        type=int,
        required=True,
        help='Patient ID to find matches for'
    )
    parser.add_argument(
        '--create',
        action='store_true',
        help='Create placement requests for matches'
    )
    parser.add_argument(
        '--max-matches',
        type=int,
        default=5,
        help='Maximum number of matches to create'
    )
    
    args = parser.parse_args()
    
    logger.info(f"Finding matches for patient {args.patient}")
    
    # Find matching therapists
    matches = find_matching_therapists(
        patient_id=args.patient
    )
    
    # Print matches
    logger.info(f"Found {len(matches)} potential matches")
    for i, match in enumerate(matches[:args.max_matches]):
        logger.info(
            f"Match {i+1}: {match['therapist_name']} "
            f"(ID: {match['therapist_id']})"
        )
    
    # Create placement requests if requested
    if args.create and matches:
        therapist_ids = [
            m['therapist_id'] for m in matches[:args.max_matches]
        ]
        request_ids = create_placement_requests(
            patient_id=args.patient,
            therapist_ids=therapist_ids,
            notes="Created via test script"
        )
        
        logger.info(f"Created {len(request_ids)} placement requests")
        for req_id in request_ids:
            logger.info(f"Created request ID: {req_id}")


if __name__ == "__main__":
    main()