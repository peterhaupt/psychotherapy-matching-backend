"""Bundle system API endpoints."""
import logging
from datetime import datetime

from flask import request
from flask_restful import Resource, reqparse
from sqlalchemy import and_, or_

from shared.api import PaginatedListResource
from ..db import get_db
from ..models import Platzsuche, Therapeutenanfrage, TherapeutAnfragePatient
from ..models.platzsuche import SearchStatus
from ..models.therapeutenanfrage import ResponseType
from ..services import BundleService, PatientService

logger = logging.getLogger(__name__)


class PlatzsucheResource(Resource):
    """REST resource for individual patient search operations."""

    def get(self, search_id):
        """Get a specific patient search by ID."""
        with get_db() as db:
            search = db.query(Platzsuche).filter_by(id=search_id).first()
            
            if not search:
                return {"message": f"Patient search {search_id} not found"}, 404
            
            # Get patient data
            patient_data = PatientService.get_patient(search.patient_id)
            
            return {
                "id": search.id,
                "patient_id": search.patient_id,
                "patient": patient_data,
                "status": search.status.value,
                "created_at": search.created_at.isoformat(),
                "updated_at": search.updated_at.isoformat() if search.updated_at else None,
                "ausgeschlossene_therapeuten": search.ausgeschlossene_therapeuten,
                "gesamt_angeforderte_kontakte": search.gesamt_angeforderte_kontakte,
                "erfolgreiche_vermittlung_datum": search.erfolgreiche_vermittlung_datum.isoformat() if search.erfolgreiche_vermittlung_datum else None,
                "notizen": search.notizen,
                "active_bundles": search.get_active_bundle_count(),
                "total_bundles": search.get_total_bundle_count()
            }, 200

    def put(self, search_id):
        """Update a patient search."""
        parser = reqparse.RequestParser()
        parser.add_argument('status', type=str)
        parser.add_argument('notizen', type=str)
        parser.add_argument('ausgeschlossene_therapeuten', type=list, location='json')
        args = parser.parse_args()
        
        with get_db() as db:
            search = db.query(Platzsuche).filter_by(id=search_id).first()
            
            if not search:
                return {"message": f"Patient search {search_id} not found"}, 404
            
            # Update fields
            if args.get('status'):
                try:
                    new_status = SearchStatus(args['status'])
                    search.status = new_status
                except ValueError:
                    return {"message": f"Invalid status: {args['status']}"}, 400
            
            if args.get('notizen') is not None:
                search.notizen = args['notizen']
            
            if args.get('ausgeschlossene_therapeuten') is not None:
                search.ausgeschlossene_therapeuten = args['ausgeschlossene_therapeuten']
            
            search.updated_at = datetime.utcnow()
            
            try:
                db.commit()
                return {"message": "Patient search updated successfully"}, 200
            except Exception as e:
                db.rollback()
                logger.error(f"Error updating patient search: {str(e)}")
                return {"message": "Failed to update patient search"}, 500


class PlatzsucheListResource(PaginatedListResource):
    """REST resource for patient search collection operations."""

    def get(self):
        """Get all patient searches with optional filtering."""
        parser = reqparse.RequestParser()
        parser.add_argument('status', type=str)
        parser.add_argument('patient_id', type=int)
        args = parser.parse_args()
        
        with get_db() as db:
            query = db.query(Platzsuche)
            
            # Apply filters
            if args.get('status'):
                try:
                    status = SearchStatus(args['status'])
                    query = query.filter(Platzsuche.status == status)
                except ValueError:
                    return {"message": f"Invalid status: {args['status']}"}, 400
            
            if args.get('patient_id'):
                query = query.filter(Platzsuche.patient_id == args['patient_id'])
            
            # Apply pagination
            page, limit = self.get_pagination_params()
            total = query.count()
            query = self.paginate_query(query)
            
            searches = query.all()
            
            return {
                "data": [{
                    "id": s.id,
                    "patient_id": s.patient_id,
                    "status": s.status.value,
                    "created_at": s.created_at.isoformat(),
                    "gesamt_angeforderte_kontakte": s.gesamt_angeforderte_kontakte,
                    "active_bundles": s.get_active_bundle_count(),
                    "total_bundles": s.get_total_bundle_count()
                } for s in searches],
                "page": page,
                "limit": limit,
                "total": total
            }, 200

    def post(self):
        """Create a new patient search."""
        parser = reqparse.RequestParser()
        parser.add_argument('patient_id', type=int, required=True)
        parser.add_argument('notizen', type=str)
        args = parser.parse_args()
        
        with get_db() as db:
            # Check if patient already has an active search
            existing = db.query(Platzsuche).filter(
                and_(
                    Platzsuche.patient_id == args['patient_id'],
                    Platzsuche.status == SearchStatus.ACTIVE
                )
            ).first()
            
            if existing:
                return {"message": "Patient already has an active search"}, 400
            
            # Create new search
            try:
                search = BundleService.create_patient_search(
                    db,
                    patient_id=args['patient_id']
                )
                
                if args.get('notizen'):
                    search.notizen = args['notizen']
                    db.commit()
                
                return {
                    "id": search.id,
                    "patient_id": search.patient_id,
                    "status": search.status.value,
                    "created_at": search.created_at.isoformat()
                }, 201
                
            except Exception as e:
                logger.error(f"Error creating patient search: {str(e)}")
                return {"message": "Failed to create patient search"}, 500


class KontaktanfrageResource(Resource):
    """REST resource for requesting additional contacts for a patient search."""

    def post(self, search_id):
        """Request additional contacts for a patient search."""
        parser = reqparse.RequestParser()
        parser.add_argument('requested_count', type=int, required=True)
        parser.add_argument('notizen', type=str)
        args = parser.parse_args()
        
        if args['requested_count'] <= 0:
            return {"message": "Requested count must be positive"}, 400
        
        with get_db() as db:
            search = db.query(Platzsuche).filter_by(id=search_id).first()
            
            if not search:
                return {"message": f"Patient search {search_id} not found"}, 404
            
            if search.status != SearchStatus.ACTIVE:
                return {"message": "Can only request contacts for active searches"}, 400
            
            # Update contact count
            search.update_contact_count(args['requested_count'])
            
            if args.get('notizen'):
                search.add_note(f"Requested {args['requested_count']} additional contacts: {args['notizen']}")
            else:
                search.add_note(f"Requested {args['requested_count']} additional contacts")
            
            try:
                db.commit()
                return {
                    "message": f"Requested {args['requested_count']} additional contacts",
                    "total_requested": search.gesamt_angeforderte_kontakte
                }, 200
            except Exception as e:
                db.rollback()
                logger.error(f"Error updating contact request: {str(e)}")
                return {"message": "Failed to update contact request"}, 500


class TherapeutenanfrageResource(Resource):
    """REST resource for individual bundle operations."""

    def get(self, bundle_id):
        """Get a specific bundle by ID."""
        with get_db() as db:
            bundle = db.query(Therapeutenanfrage).filter_by(id=bundle_id).first()
            
            if not bundle:
                return {"message": f"Bundle {bundle_id} not found"}, 404
            
            # Get patient details
            patients = []
            for bp in bundle.bundle_patients:
                patient_data = PatientService.get_patient(bp.patient_id)
                patients.append({
                    "position": bp.position_im_buendel,
                    "patient_id": bp.patient_id,
                    "patient": patient_data,
                    "platzsuche_id": bp.platzsuche_id,
                    "status": bp.status.value,
                    "antwortergebnis": bp.antwortergebnis.value if bp.antwortergebnis else None,
                    "antwortnotizen": bp.antwortnotizen
                })
            
            return {
                "id": bundle.id,
                "therapist_id": bundle.therapist_id,
                "created_date": bundle.created_date.isoformat(),
                "sent_date": bundle.sent_date.isoformat() if bundle.sent_date else None,
                "response_date": bundle.response_date.isoformat() if bundle.response_date else None,
                "antworttyp": bundle.antworttyp.value if bundle.antworttyp else None,
                "buendelgroesse": bundle.buendelgroesse,
                "angenommen_anzahl": bundle.angenommen_anzahl,
                "abgelehnt_anzahl": bundle.abgelehnt_anzahl,
                "keine_antwort_anzahl": bundle.keine_antwort_anzahl,
                "notizen": bundle.notizen,
                "email_id": bundle.email_id,
                "phone_call_id": bundle.phone_call_id,
                "patients": patients,
                "needs_follow_up": bundle.needs_follow_up()
            }, 200


class TherapeutenanfrageListResource(PaginatedListResource):
    """REST resource for bundle collection operations."""

    def get(self):
        """Get all bundles with optional filtering."""
        parser = reqparse.RequestParser()
        parser.add_argument('therapist_id', type=int)
        parser.add_argument('sent_status', type=str)  # sent, unsent
        parser.add_argument('response_status', type=str)  # responded, pending
        args = parser.parse_args()
        
        with get_db() as db:
            query = db.query(Therapeutenanfrage)
            
            # Apply filters
            if args.get('therapist_id'):
                query = query.filter(Therapeutenanfrage.therapist_id == args['therapist_id'])
            
            if args.get('sent_status'):
                if args['sent_status'] == 'sent':
                    query = query.filter(Therapeutenanfrage.sent_date.isnot(None))
                elif args['sent_status'] == 'unsent':
                    query = query.filter(Therapeutenanfrage.sent_date.is_(None))
            
            if args.get('response_status'):
                if args['response_status'] == 'responded':
                    query = query.filter(Therapeutenanfrage.response_date.isnot(None))
                elif args['response_status'] == 'pending':
                    query = query.filter(
                        and_(
                            Therapeutenanfrage.sent_date.isnot(None),
                            Therapeutenanfrage.response_date.is_(None)
                        )
                    )
            
            # Apply pagination
            page, limit = self.get_pagination_params()
            total = query.count()
            query = self.paginate_query(query)
            
            bundles = query.all()
            
            return {
                "data": [{
                    "id": b.id,
                    "therapist_id": b.therapist_id,
                    "created_date": b.created_date.isoformat(),
                    "sent_date": b.sent_date.isoformat() if b.sent_date else None,
                    "response_date": b.response_date.isoformat() if b.response_date else None,
                    "antworttyp": b.antworttyp.value if b.antworttyp else None,
                    "buendelgroesse": b.buendelgroesse,
                    "needs_follow_up": b.needs_follow_up()
                } for b in bundles],
                "page": page,
                "limit": limit,
                "total": total
            }, 200


class BundleCreationResource(Resource):
    """REST resource for triggering bundle creation."""

    def post(self):
        """Trigger bundle creation for all eligible therapists."""
        # Note: This is a placeholder that returns 501
        # The actual implementation will call the bundle algorithm
        return {
            "message": "Bundle creation algorithm not yet implemented",
            "note": "This will trigger the creation of bundles for all eligible therapists"
        }, 501


class BundleResponseResource(Resource):
    """REST resource for recording therapist responses to bundles."""

    def put(self, bundle_id):
        """Record a therapist's response to a bundle."""
        parser = reqparse.RequestParser()
        parser.add_argument('patient_responses', type=dict, required=True, location='json')
        parser.add_argument('notizen', type=str)
        args = parser.parse_args()
        
        with get_db() as db:
            # Validate bundle exists
            bundle = db.query(Therapeutenanfrage).filter_by(id=bundle_id).first()
            if not bundle:
                return {"message": f"Bundle {bundle_id} not found"}, 404
            
            # Validate patient responses
            patient_responses = {}
            for patient_id_str, outcome_str in args['patient_responses'].items():
                try:
                    patient_id = int(patient_id_str)
                    # Import here to avoid circular import
                    from ..models.therapeut_anfrage_patient import PatientOutcome
                    outcome = PatientOutcome(outcome_str)
                    patient_responses[patient_id] = outcome
                except (ValueError, KeyError):
                    return {
                        "message": f"Invalid patient response: {patient_id_str} -> {outcome_str}"
                    }, 400
            
            # Handle the response
            try:
                BundleService.handle_bundle_response(
                    db,
                    bundle_id=bundle_id,
                    patient_responses=patient_responses,
                    notes=args.get('notizen')
                )
                
                return {"message": "Bundle response recorded successfully"}, 200
                
            except Exception as e:
                logger.error(f"Error recording bundle response: {str(e)}")
                return {"message": "Failed to record bundle response"}, 500