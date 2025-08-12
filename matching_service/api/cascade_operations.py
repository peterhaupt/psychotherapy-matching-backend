"""Cascade operations API endpoints for handling cross-service synchronous updates.

These endpoints replace Kafka event-driven communication with direct API calls
to handle cascading operations when entities are modified in other services.
"""
import logging
from flask import request
from flask_restful import Resource, reqparse
from sqlalchemy import and_

from db import get_db_context
from models import Platzsuche, Therapeutenanfrage
from models.platzsuche import SuchStatus

# Initialize logging
logger = logging.getLogger(__name__)


class PatientDeletedCascadeResource(Resource):
    """Handle cascading operations when a patient is deleted from the system."""
    
    def post(self):
        """Cancel all active searches for a deleted patient.
        
        This endpoint is called by the Patient Service when a patient is deleted.
        It ensures all active searches (Platzsuche) for the patient are cancelled.
        
        Returns:
            200: Searches cancelled successfully
            500: Failed to cancel searches
        """
        parser = reqparse.RequestParser()
        parser.add_argument('patient_id', type=int, required=True, location='json')
        args = parser.parse_args()
        
        patient_id = args['patient_id']
        logger.info(f"Processing patient deletion cascade for patient {patient_id}")
        
        try:
            with get_db_context() as db:
                # Find all active searches for this patient
                active_searches = db.query(Platzsuche).filter(
                    and_(
                        Platzsuche.patient_id == patient_id,
                        Platzsuche.status == SuchStatus.aktiv
                    )
                ).all()
                
                cancelled_count = 0
                for search in active_searches:
                    # Cancel the search
                    search.status = SuchStatus.abgebrochen
                    search.add_note("Cancelled: Patient deleted from system", author="System")
                    cancelled_count += 1
                    logger.info(f"Cancelled search {search.id} for deleted patient {patient_id}")
                
                db.commit()
                
                logger.info(f"Successfully cancelled {cancelled_count} active searches for patient {patient_id}")
                
                return {
                    "message": f"Cancelled {cancelled_count} active searches",
                    "patient_id": patient_id,
                    "cancelled_searches": cancelled_count
                }, 200
                
        except Exception as e:
            logger.error(f"Failed to process patient deletion cascade for patient {patient_id}: {str(e)}", exc_info=True)
            return {
                "message": f"Failed to cancel searches: {str(e)}",
                "patient_id": patient_id
            }, 500


class TherapistBlockedCascadeResource(Resource):
    """Handle cascading operations when a therapist is blocked."""
    
    def post(self):
        """Process therapist blocking by cancelling unsent anfragen and updating exclusions.
        
        This endpoint is called by the Therapist Service when a therapist is blocked.
        It cancels all unsent anfragen and adds the therapist to exclusion lists
        for patients with pending anfragen.
        
        Returns:
            200: Blocking processed successfully
            500: Failed to process blocking
        """
        parser = reqparse.RequestParser()
        parser.add_argument('therapist_id', type=int, required=True, location='json')
        parser.add_argument('reason', type=str, required=False, location='json')
        args = parser.parse_args()
        
        therapist_id = args['therapist_id']
        reason = args.get('reason', 'Therapist blocked')
        logger.info(f"Processing therapist blocking cascade for therapist {therapist_id}: {reason}")
        
        try:
            with get_db_context() as db:
                # Cancel all unsent anfragen for this therapist
                unsent_anfragen = db.query(Therapeutenanfrage).filter(
                    and_(
                        Therapeutenanfrage.therapist_id == therapist_id,
                        Therapeutenanfrage.gesendet_datum.is_(None)
                    )
                ).all()
                
                cancelled_anfragen_count = 0
                for anfrage in unsent_anfragen:
                    anfrage.add_note(f"Cancelled: {reason}", author="System")
                    cancelled_anfragen_count += 1
                    logger.info(f"Cancelled unsent anfrage {anfrage.id} for blocked therapist {therapist_id}")
                
                # Find sent but unanswered anfragen to update patient exclusion lists
                pending_anfragen = db.query(Therapeutenanfrage).filter(
                    and_(
                        Therapeutenanfrage.therapist_id == therapist_id,
                        Therapeutenanfrage.gesendet_datum.isnot(None),
                        Therapeutenanfrage.antwort_datum.is_(None)
                    )
                ).all()
                
                updated_searches_count = 0
                for anfrage in pending_anfragen:
                    # Add therapist to exclusion list for each patient in the anfrage
                    for anfrage_patient in anfrage.anfrage_patients:
                        if anfrage_patient.platzsuche and anfrage_patient.platzsuche.status == SuchStatus.aktiv:
                            anfrage_patient.platzsuche.exclude_therapist(
                                therapist_id,
                                reason=f"Therapist blocked: {reason}"
                            )
                            updated_searches_count += 1
                            logger.debug(f"Added therapist {therapist_id} to exclusion list for search {anfrage_patient.platzsuche.id}")
                
                db.commit()
                
                logger.info(
                    f"Successfully processed therapist blocking for therapist {therapist_id}: "
                    f"cancelled {cancelled_anfragen_count} anfragen, "
                    f"updated {updated_searches_count} patient exclusion lists"
                )
                
                return {
                    "message": "Processed therapist blocking",
                    "therapist_id": therapist_id,
                    "cancelled_anfragen": cancelled_anfragen_count,
                    "updated_exclusion_lists": updated_searches_count
                }, 200
                
        except Exception as e:
            logger.error(f"Failed to process therapist blocking cascade for therapist {therapist_id}: {str(e)}", exc_info=True)
            return {
                "message": f"Failed to process blocking: {str(e)}",
                "therapist_id": therapist_id
            }, 500


class TherapistUnblockedCascadeResource(Resource):
    """Handle cascading operations when a therapist is unblocked."""
    
    def post(self):
        """Process therapist unblocking.
        
        This endpoint is called by the Therapist Service when a therapist is unblocked.
        Currently, this is a minimal implementation as we don't automatically remove
        therapists from exclusion lists (requires manual review).
        
        Returns:
            200: Unblocking processed successfully
            500: Failed to process unblocking
        """
        parser = reqparse.RequestParser()
        parser.add_argument('therapist_id', type=int, required=True, location='json')
        args = parser.parse_args()
        
        therapist_id = args['therapist_id']
        logger.info(f"Processing therapist unblocking cascade for therapist {therapist_id}")
        
        try:
            # Currently minimal implementation
            # We don't automatically remove from exclusion lists as this requires manual review
            # Future enhancement: Could notify admin or create review tasks
            
            logger.info(f"Therapist unblocking processed for therapist {therapist_id} (no automatic exclusion removal)")
            
            return {
                "message": "Therapist unblocking processed",
                "therapist_id": therapist_id,
                "note": "Exclusion lists not automatically updated - requires manual review"
            }, 200
            
        except Exception as e:
            logger.error(f"Failed to process therapist unblocking cascade for therapist {therapist_id}: {str(e)}", exc_info=True)
            return {
                "message": f"Failed to process unblocking: {str(e)}",
                "therapist_id": therapist_id
            }, 500