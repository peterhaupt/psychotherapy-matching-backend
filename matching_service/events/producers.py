"""Producer for matching-related Kafka events - Bundle System."""
import logging
from typing import Dict, Any, List, Optional

from shared.kafka.robust_producer import RobustKafkaProducer

# Initialize logging
logger = logging.getLogger(__name__)

# Initialize Kafka producer
producer = RobustKafkaProducer(service_name="matching-service")

# Topic for matching events
MATCHING_TOPIC = "matching-events"


def publish_bundle_created(
    bundle_id: int,
    therapist_id: int,
    patient_ids: List[int],
    bundle_size: int
) -> bool:
    """Publish an event when a new bundle is created.

    Args:
        bundle_id: ID of the created bundle (therapeutenanfrage)
        therapist_id: ID of the therapist
        patient_ids: List of patient IDs in the bundle
        bundle_size: Number of patients in the bundle

    Returns:
        bool: True if publishing was successful, False otherwise
    """
    return producer.send_event(
        topic=MATCHING_TOPIC,
        event_type="bundle.created",
        payload={
            "bundle_id": bundle_id,
            "therapist_id": therapist_id,
            "patient_ids": patient_ids,
            "bundle_size": bundle_size
        },
        key=str(bundle_id)
    )


def publish_bundle_sent(
    bundle_id: int,
    communication_type: str,
    communication_id: Optional[int] = None
) -> bool:
    """Publish an event when a bundle is sent to therapist.

    Args:
        bundle_id: ID of the bundle
        communication_type: Type of communication (email/phone)
        communication_id: ID of the email or phone call

    Returns:
        bool: True if publishing was successful, False otherwise
    """
    return producer.send_event(
        topic=MATCHING_TOPIC,
        event_type="bundle.sent",
        payload={
            "bundle_id": bundle_id,
            "communication_type": communication_type,
            "communication_id": communication_id
        },
        key=str(bundle_id)
    )


def publish_bundle_response_received(
    bundle_id: int,
    response_type: str,
    accepted_count: int,
    rejected_count: int,
    no_response_count: int
) -> bool:
    """Publish an event when a bundle response is received.

    Args:
        bundle_id: ID of the bundle
        response_type: Type of response (full_acceptance/partial_acceptance/full_rejection)
        accepted_count: Number of accepted patients
        rejected_count: Number of rejected patients
        no_response_count: Number of patients with no response

    Returns:
        bool: True if publishing was successful, False otherwise
    """
    return producer.send_event(
        topic=MATCHING_TOPIC,
        event_type="bundle.response_received",
        payload={
            "bundle_id": bundle_id,
            "response_type": response_type,
            "accepted_count": accepted_count,
            "rejected_count": rejected_count,
            "no_response_count": no_response_count
        },
        key=str(bundle_id)
    )


def publish_search_status_changed(
    search_id: int,
    patient_id: int,
    old_status: str,
    new_status: str
) -> bool:
    """Publish an event when a patient search status changes.

    Args:
        search_id: ID of the platzsuche
        patient_id: ID of the patient
        old_status: Previous status
        new_status: New status

    Returns:
        bool: True if publishing was successful, False otherwise
    """
    return producer.send_event(
        topic=MATCHING_TOPIC,
        event_type="search.status_changed",
        payload={
            "search_id": search_id,
            "patient_id": patient_id,
            "old_status": old_status,
            "new_status": new_status
        },
        key=str(search_id)
    )


def publish_cooling_period_started(
    therapist_id: int,
    next_contactable_date: str,
    reason: str
) -> bool:
    """Publish an event when a cooling period starts for a therapist.

    Args:
        therapist_id: ID of the therapist
        next_contactable_date: Date when therapist can be contacted again
        reason: Reason for cooling period (response_received/manual)

    Returns:
        bool: True if publishing was successful, False otherwise
    """
    return producer.send_event(
        topic=MATCHING_TOPIC,
        event_type="cooling.period_started",
        payload={
            "therapist_id": therapist_id,
            "next_contactable_date": next_contactable_date,
            "reason": reason
        },
        key=str(therapist_id)
    )