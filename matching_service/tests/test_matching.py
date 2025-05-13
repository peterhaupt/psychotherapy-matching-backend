"""Test script for the matching algorithm."""
import sys
import os
import logging
import json
from argparse import ArgumentParser

# Add the project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from algorithms.matcher import (
    find_matching_therapists,
    create_placement_requests,
    calculate_distance
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_distance_calculation():
    """Test the distance calculation between two points."""
    # Berlin coordinates
    berlin = "Berlin, Germany"
    # Munich coordinates
    munich = "Munich, Germany"
    
    # Calculate distance between Berlin and Munich
    result = calculate_distance(berlin, munich)
    
    logger.info(f"Distance from Berlin to Munich:")
    logger.info(f"  Distance: {result['distance_km']:.2f} km")
    logger.info(f"  Travel time: {result['travel_time_minutes']:.2f} minutes")
    logger.info(f"  Source: {result['source']}")
    
    return result


def main():
    """Run the matching algorithm test."""
    parser = ArgumentParser(description="Test the matching algorithm")
    parser.add_argument(
        '--patient',
        type=int,
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
    parser.add_argument(
        '--test-distance',
        action='store_true',
        help='Test distance calculation'
    )
    
    args = parser.parse_args()
    
    if args.test_distance:
        logger.info("Testing distance calculation...")
        test_distance_calculation()
        return
    
    if not args.patient:
        logger.error("Patient ID is required unless testing distance calculation")
        parser.print_help()
        return
    
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
            f"(ID: {match['therapist_id']}) - "
            f"Distance: {match['distance_km']:.2f} km, "
            f"Travel time: {match['travel_time_minutes']:.2f} min"
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