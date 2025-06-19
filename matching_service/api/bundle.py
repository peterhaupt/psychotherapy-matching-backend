"""Bundle system API endpoints - FULLY IMPLEMENTED."""
import logging
from datetime import datetime

from flask import request, jsonify
from flask_restful import Resource, reqparse
from sqlalchemy import and_, or_, desc
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from shared.api import PaginatedListResource
from db import get_db
from models import Platzsuche, Therapeutenanfrage, TherapeutAnfragePatient
from models.platzsuche import SuchStatus
from models.therapeutenanfrage import AntwortTyp
from models.therapeut_anfrage_patient import BuendelPatientStatus, PatientenErgebnis
from services import BundleService, PatientService, TherapistService
from events.producers import (
    publish_bundle_created,
    publish_bundle_sent,
    publish_bundle_response_received,
    publish_search_status_changed
)
from algorithms.bundle_creator import create_bundles_for_all_therapists

logger = logging.getLogger(__name__)


class PlatzsucheResource(Resource):
    """REST resource for individual patient search operations."""

    def get(self, search_id):
        """Get a specific patient search by ID."""
        try:
            with get_db() as db:
                search = db.query(Platzsuche).filter_by(id=search_id).first()
                
                if not search:
                    return {"message": f"Patient search {search_id} not found"}, 404
                
                # Get patient data from Patient Service
                patient_data = PatientService.get_patient(search.patient_id)
                if not patient_data:
                    logger.warning(f"Could not fetch patient data for patient_id {search.patient_id}")
                
                # Get bundle history
                bundle_entries = []
                for entry in search.bundle_entries:
                    bundle = entry.therapeutenanfrage
                    therapist = TherapistService.get_therapist(bundle.therapist_id)
                    
                    bundle_entries.append({
                        "bundle_id": bundle.id,
                        "therapist_id": bundle.therapist_id,
                        "therapeuten_name": f"{therapist.get('vorname', '')} {therapist.get('nachname', '')}" if therapist else "Unknown",
                        "position": entry.position_im_buendel,
                        "status": entry.status.value,
                        "outcome": entry.antwortergebnis.value if entry.antwortergebnis else None,
                        "sent_date": bundle.gesendet_datum.isoformat() if bundle.gesendet_datum else None,
                        "response_date": bundle.antwort_datum.isoformat() if bundle.antwort_datum else None
                    })
                
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
                    "aktive_buendel": search.get_active_bundle_count(),
                    "gesamt_buendel": search.get_total_bundle_count(),
                    "buendel_verlauf": bundle_entries
                }, 200
                
        except Exception as e:
            logger.error(f"Error fetching patient search {search_id}: {str(e)}")
            return {"message": "Internal server error"}, 500

    def put(self, search_id):
        """Update a patient search."""
        parser = reqparse.RequestParser()
        parser.add_argument('status', type=str)
        parser.add_argument('notizen', type=str)
        parser.add_argument('ausgeschlossene_therapeuten', type=list, location='json')
        args = parser.parse_args()
        
        try:
            with get_db() as db:
                search = db.query(Platzsuche).filter_by(id=search_id).first()
                
                if not search:
                    return {"message": f"Patient search {search_id} not found"}, 404
                
                old_status = search.status
                
                # Update fields
                if args.get('status'):
                    try:
                        new_status = SuchStatus[args['status']]
                        search.status = new_status
                        
                        # Publish status change event
                        if old_status != new_status:
                            publish_search_status_changed(
                                search.id,
                                search.patient_id,
                                old_status.value,
                                new_status.value
                            )
                    except KeyError:
                        valid_values = [status.value for status in SuchStatus]
                        return {"message": f"Invalid status '{args['status']}'. Valid values: {valid_values}"}, 400
                
                if args.get('notizen') is not None:
                    search.notizen = args['notizen']
                
                if args.get('ausgeschlossene_therapeuten') is not None:
                    # Validate therapist IDs
                    therapist_ids = args['ausgeschlossene_therapeuten']
                    if not all(isinstance(tid, int) for tid in therapist_ids):
                        return {"message": "Invalid therapist IDs in exclusion list"}, 400
                    search.ausgeschlossene_therapeuten = therapist_ids
                
                search.updated_at = datetime.utcnow()
                
                db.commit()
                return {"message": "Patient search updated successfully", "id": search.id}, 200
                
        except IntegrityError as e:
            logger.error(f"Integrity error updating patient search: {str(e)}")
            return {"message": "Data integrity error"}, 400
        except Exception as e:
            logger.error(f"Error updating patient search: {str(e)}")
            return {"message": "Internal server error"}, 500

    def delete(self, search_id):
        """Cancel a patient search."""
        try:
            with get_db() as db:
                search = db.query(Platzsuche).filter_by(id=search_id).first()
                
                if not search:
                    return {"message": f"Patient search {search_id} not found"}, 404
                
                # Cancel the search instead of deleting
                old_status = search.status
                search.cancel_search("Cancelled via API")
                
                # Publish cancellation event
                publish_search_status_changed(
                    search.id,
                    search.patient_id,
                    old_status.value,
                    SuchStatus.abgebrochen.value
                )
                
                db.commit()
                return {"message": "Patient search cancelled successfully"}, 200
                
        except Exception as e:
            logger.error(f"Error cancelling patient search: {str(e)}")
            return {"message": "Internal server error"}, 500


class PlatzsucheListResource(PaginatedListResource):
    """REST resource for patient search collection operations."""

    def get(self):
        """Get all patient searches with optional filtering."""
        parser = reqparse.RequestParser()
        parser.add_argument('status', type=str, location='args')
        parser.add_argument('patient_id', type=int, location='args')
        parser.add_argument('min_bundles', type=int, location='args')
        parser.add_argument('max_bundles', type=int, location='args')
        args = parser.parse_args()
        
        try:
            with get_db() as db:
                query = db.query(Platzsuche)
                
                # Apply filters
                if args.get('status'):
                    try:
                        status = SuchStatus[args['status']]
                        query = query.filter(Platzsuche.status == status)
                    except KeyError:
                        valid_values = [s.value for s in SuchStatus]
                        return {"message": f"Invalid status '{args['status']}'. Valid values: {valid_values}"}, 400
                
                if args.get('patient_id'):
                    query = query.filter(Platzsuche.patient_id == args['patient_id'])
                
                # Order by creation date (newest first)
                query = query.order_by(desc(Platzsuche.created_at))
                
                # Apply pagination
                page, limit = self.get_pagination_params()
                total = query.count()
                query = self.paginate_query(query)
                
                searches = query.all()
                
                # Filter by bundle count if specified
                if args.get('min_bundles') is not None or args.get('max_bundles') is not None:
                    filtered_searches = []
                    for s in searches:
                        bundle_count = s.get_total_bundle_count()
                        if args.get('min_bundles') is not None and bundle_count < args['min_bundles']:
                            continue
                        if args.get('max_bundles') is not None and bundle_count > args['max_bundles']:
                            continue
                        filtered_searches.append(s)
                    searches = filtered_searches
                    total = len(searches)  # Adjust total for filtered results
                
                # Get patient data for all searches
                patient_ids = [s.patient_id for s in searches]
                patients = PatientService.get_patients(patient_ids)
                
                return {
                    "data": [{
                        "id": s.id,
                        "patient_id": s.patient_id,
                        "patienten_name": f"{patients.get(s.patient_id, {}).get('vorname', '')} {patients.get(s.patient_id, {}).get('nachname', '')}" if s.patient_id in patients else "Unknown",
                        "status": s.status.value,
                        "created_at": s.created_at.isoformat(),
                        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
                        "gesamt_angeforderte_kontakte": s.gesamt_angeforderte_kontakte,
                        "aktive_buendel": s.get_active_bundle_count(),
                        "gesamt_buendel": s.get_total_bundle_count(),
                        "ausgeschlossene_therapeuten_anzahl": len(s.ausgeschlossene_therapeuten) if s.ausgeschlossene_therapeuten else 0
                    } for s in searches],
                    "page": page,
                    "limit": limit,
                    "total": total
                }, 200
                
        except Exception as e:
            logger.error(f"Error fetching patient searches: {str(e)}")
            return {"message": "Internal server error"}, 500

    def post(self):
        """Create a new patient search."""
        parser = reqparse.RequestParser()
        parser.add_argument('patient_id', type=int, required=True)
        parser.add_argument('notizen', type=str)
        args = parser.parse_args()
        
        try:
            with get_db() as db:
                # Verify patient exists
                patient = PatientService.get_patient(args['patient_id'])
                if not patient:
                    return {"message": f"Patient {args['patient_id']} not found"}, 404
                
                # Check if patient already has an active search
                existing = db.query(Platzsuche).filter(
                    and_(
                        Platzsuche.patient_id == args['patient_id'],
                        Platzsuche.status == SuchStatus.aktiv
                    )
                ).first()
                
                if existing:
                    return {
                        "message": "Patient already has an active search",
                        "search_id": existing.id
                    }, 400
                
                # Create new search
                search = BundleService.create_patient_search(
                    db,
                    patient_id=args['patient_id']
                )
                
                if args.get('notizen'):
                    search.add_note(args['notizen'], author="API")
                    db.commit()
                
                # Publish creation event
                publish_search_status_changed(
                    search.id,
                    search.patient_id,
                    None,
                    SuchStatus.aktiv.value
                )
                
                return {
                    "id": search.id,
                    "patient_id": search.patient_id,
                    "status": search.status.value,
                    "created_at": search.created_at.isoformat(),
                    "message": "Patient search created successfully"
                }, 201
                
        except IntegrityError as e:
            logger.error(f"Integrity error creating patient search: {str(e)}")
            return {"message": "Patient search already exists"}, 400
        except Exception as e:
            logger.error(f"Error creating patient search: {str(e)}")
            return {"message": "Internal server error"}, 500


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
        
        if args['requested_count'] > 100:
            return {"message": "Requested count too high (max: 100)"}, 400
        
        try:
            with get_db() as db:
                search = db.query(Platzsuche).filter_by(id=search_id).first()
                
                if not search:
                    return {"message": f"Patient search {search_id} not found"}, 404
                
                if search.status != SuchStatus.aktiv:
                    return {
                        "message": f"Can only request contacts for active searches. Current status: {search.status.value}"
                    }, 400
                
                # Update contact count
                old_count = search.gesamt_angeforderte_kontakte
                search.update_contact_count(args['requested_count'])
                
                # Add note
                note = f"Requested {args['requested_count']} additional contacts (total: {search.gesamt_angeforderte_kontakte})"
                if args.get('notizen'):
                    note += f" - {args['notizen']}"
                search.add_note(note, author="API")
                
                db.commit()
                
                logger.info(
                    f"Contact request for search {search_id}: "
                    f"requested {args['requested_count']}, "
                    f"total now {search.gesamt_angeforderte_kontakte}"
                )
                
                return {
                    "message": f"Requested {args['requested_count']} additional contacts",
                    "previous_total": old_count,
                    "new_total": search.gesamt_angeforderte_kontakte,
                    "search_id": search.id
                }, 200
                
        except Exception as e:
            logger.error(f"Error updating contact request: {str(e)}")
            return {"message": "Internal server error"}, 500


class TherapeutenanfrageResource(Resource):
    """REST resource for individual bundle operations."""

    def get(self, bundle_id):
        """Get a specific bundle by ID with full details."""
        try:
            with get_db() as db:
                bundle = db.query(Therapeutenanfrage).filter_by(id=bundle_id).first()
                
                if not bundle:
                    return {"message": f"Bundle {bundle_id} not found"}, 404
                
                # Get therapist data
                therapist_data = TherapistService.get_therapist(bundle.therapist_id)
                if not therapist_data:
                    logger.warning(f"Could not fetch therapist data for therapist_id {bundle.therapist_id}")
                
                # Get patient details
                patients = []
                for bp in bundle.bundle_patients:
                    patient_data = PatientService.get_patient(bp.patient_id)
                    
                    # Get the platzsuche data
                    search = db.query(Platzsuche).filter_by(id=bp.platzsuche_id).first()
                    
                    patients.append({
                        "position": bp.position_im_buendel,
                        "patient_id": bp.patient_id,
                        "patient": patient_data,
                        "platzsuche_id": bp.platzsuche_id,
                        "search_created_at": search.created_at.isoformat() if search else None,
                        "wartezeit_tage": (datetime.utcnow() - search.created_at).days if search else None,
                        "status": bp.status.value,
                        "antwortergebnis": bp.antwortergebnis.value if bp.antwortergebnis else None,
                        "antwortnotizen": bp.antwortnotizen
                    })
                
                # Sort patients by position
                patients.sort(key=lambda x: x['position'])
                
                # Calculate response summary
                response_summary = {
                    "total_accepted": bundle.angenommen_anzahl,
                    "total_rejected": bundle.abgelehnt_anzahl,
                    "total_no_response": bundle.keine_antwort_anzahl,
                    "antwort_vollstaendig": bundle.is_response_complete()
                }
                
                return {
                    "id": bundle.id,
                    "therapist_id": bundle.therapist_id,
                    "therapist": therapist_data,
                    "erstellt_datum": bundle.erstellt_datum.isoformat(),
                    "gesendet_datum": bundle.gesendet_datum.isoformat() if bundle.gesendet_datum else None,
                    "antwort_datum": bundle.antwort_datum.isoformat() if bundle.antwort_datum else None,
                    "tage_seit_versand": bundle.days_since_sent(),
                    "antworttyp": bundle.antworttyp.value if bundle.antworttyp else None,
                    "buendelgroesse": bundle.buendelgroesse,
                    "antwort_zusammenfassung": response_summary,
                    "notizen": bundle.notizen,
                    "email_id": bundle.email_id,
                    "phone_call_id": bundle.phone_call_id,
                    "patients": patients,
                    "nachverfolgung_erforderlich": bundle.needs_follow_up()
                }, 200
                
        except Exception as e:
            logger.error(f"Error fetching bundle {bundle_id}: {str(e)}")
            return {"message": "Internal server error"}, 500


class TherapeutenanfrageListResource(PaginatedListResource):
    """REST resource for bundle collection operations."""

    def get(self):
        """Get all bundles with optional filtering."""
        parser = reqparse.RequestParser()
        parser.add_argument('therapist_id', type=int, location='args')
        parser.add_argument('versand_status', type=str, location='args')
        parser.add_argument('antwort_status', type=str, location='args')
        parser.add_argument('nachverfolgung_erforderlich', type=bool, location='args')
        parser.add_argument('min_size', type=int, location='args')
        parser.add_argument('max_size', type=int, location='args')
        args = parser.parse_args()
        
        try:
            with get_db() as db:
                query = db.query(Therapeutenanfrage)
                
                # Apply filters
                if args.get('therapist_id'):
                    query = query.filter(Therapeutenanfrage.therapist_id == args['therapist_id'])
                
                if args.get('versand_status'):
                    if args['versand_status'] == 'gesendet':
                        query = query.filter(Therapeutenanfrage.gesendet_datum.isnot(None))
                    elif args['versand_status'] == 'ungesendet':
                        query = query.filter(Therapeutenanfrage.gesendet_datum.is_(None))
                    else:
                        return {"message": "Invalid versand_status. Use 'gesendet' or 'ungesendet'"}, 400
                
                if args.get('antwort_status'):
                    if args['antwort_status'] == 'beantwortet':
                        query = query.filter(Therapeutenanfrage.antwort_datum.isnot(None))
                    elif args['antwort_status'] == 'ausstehend':
                        query = query.filter(
                            and_(
                                Therapeutenanfrage.gesendet_datum.isnot(None),
                                Therapeutenanfrage.antwort_datum.is_(None)
                            )
                        )
                    else:
                        return {"message": "Invalid antwort_status. Use 'beantwortet' or 'ausstehend'"}, 400
                
                if args.get('min_size'):
                    query = query.filter(Therapeutenanfrage.buendelgroesse >= args['min_size'])
                
                if args.get('max_size'):
                    query = query.filter(Therapeutenanfrage.buendelgroesse <= args['max_size'])
                
                # Order by creation date (newest first)
                query = query.order_by(desc(Therapeutenanfrage.erstellt_datum))
                
                # Apply pagination
                page, limit = self.get_pagination_params()
                total = query.count()
                query = self.paginate_query(query)
                
                bundles = query.all()
                
                # Filter by nachverfolgung_erforderlich if specified
                if args.get('nachverfolgung_erforderlich') is not None:
                    bundles = [b for b in bundles if b.needs_follow_up() == args['nachverfolgung_erforderlich']]
                    if args['nachverfolgung_erforderlich']:
                        total = len(bundles)  # Adjust total for filtered results
                
                # Get therapist data
                therapist_ids = list(set(b.therapist_id for b in bundles))
                therapists = {}
                for tid in therapist_ids:
                    therapist_data = TherapistService.get_therapist(tid)
                    if therapist_data:
                        therapists[tid] = therapist_data
                
                return {
                    "data": [{
                        "id": b.id,
                        "therapist_id": b.therapist_id,
                        "therapeuten_name": f"{therapists.get(b.therapist_id, {}).get('vorname', '')} {therapists.get(b.therapist_id, {}).get('nachname', '')}" if b.therapist_id in therapists else "Unknown",
                        "erstellt_datum": b.erstellt_datum.isoformat(),
                        "gesendet_datum": b.gesendet_datum.isoformat() if b.gesendet_datum else None,
                        "antwort_datum": b.antwort_datum.isoformat() if b.antwort_datum else None,
                        "tage_seit_versand": b.days_since_sent(),
                        "antworttyp": b.antworttyp.value if b.antworttyp else None,
                        "buendelgroesse": b.buendelgroesse,
                        "angenommen_anzahl": b.angenommen_anzahl,
                        "abgelehnt_anzahl": b.abgelehnt_anzahl,
                        "keine_antwort_anzahl": b.keine_antwort_anzahl,
                        "nachverfolgung_erforderlich": b.needs_follow_up(),
                        "antwort_vollstaendig": b.is_response_complete()
                    } for b in bundles],
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "summary": {
                        "total_bundles": total,
                        "unsent_bundles": sum(1 for b in bundles if not b.gesendet_datum),
                        "pending_responses": sum(1 for b in bundles if b.gesendet_datum and not b.antwort_datum),
                        "needing_follow_up": sum(1 for b in bundles if b.needs_follow_up())
                    }
                }, 200
                
        except Exception as e:
            logger.error(f"Error fetching bundles: {str(e)}")
            return {"message": "Internal server error"}, 500


class BundleCreationResource(Resource):
    """REST resource for triggering bundle creation."""

    def post(self):
        """Trigger bundle creation for all eligible therapists."""
        parser = reqparse.RequestParser()
        parser.add_argument('sofort_senden', type=bool, default=False)  # Changed from send_immediately
        parser.add_argument('testlauf', type=bool, default=False)  # Changed from dry_run
        parser.add_argument('therapist_ids', type=list, location='json')  # Optional: specific therapists
        args = parser.parse_args()
        
        try:
            with get_db() as db:
                # Create bundles
                logger.info(f"Starting bundle creation (testlauf={args.get('testlauf')})")
                
                bundles = create_bundles_for_all_therapists(db)
                
                # Filter by specific therapist IDs if provided
                if args.get('therapist_ids'):
                    bundles = [b for b in bundles if b.therapist_id in args['therapist_ids']]
                
                logger.info(f"Created {len(bundles)} bundles")
                
                if args.get('testlauf'):
                    # Don't commit in test run mode
                    bundle_data = []
                    for b in bundles:
                        # Get patient IDs for this bundle
                        patient_ids = [bp.patient_id for bp in b.bundle_patients]
                        
                        # Get therapist name
                        therapist = TherapistService.get_therapist(b.therapist_id)
                        therapist_name = f"{therapist.get('vorname', '')} {therapist.get('nachname', '')}" if therapist else "Unknown"
                        
                        bundle_data.append({
                            "therapist_id": b.therapist_id,
                            "therapeuten_name": therapist_name,
                            "bundle_size": b.buendelgroesse,
                            "patient_ids": patient_ids
                        })
                    
                    db.rollback()
                    return {
                        "message": "Testlauf completed - no data was saved",
                        "buendel_erstellt": len(bundles),
                        "bundles": bundle_data
                    }, 200
                
                # Commit the bundles
                db.commit()
                
                # Publish creation events
                for bundle in bundles:
                    patient_ids = [bp.patient_id for bp in bundle.bundle_patients]
                    publish_bundle_created(
                        bundle.id,
                        bundle.therapist_id,
                        patient_ids,
                        bundle.buendelgroesse
                    )
                
                # Send bundles if requested
                sent_count = 0
                send_errors = []
                
                if args.get('sofort_senden') and bundles:
                    logger.info(f"Sending {len(bundles)} bundles immediately")
                    
                    for bundle in bundles:
                        try:
                            success = BundleService.send_bundle(db, bundle.id)
                            if success:
                                sent_count += 1
                                # Publish sent event
                                publish_bundle_sent(
                                    bundle.id,
                                    "email",
                                    bundle.email_id
                                )
                            else:
                                send_errors.append({
                                    "bundle_id": bundle.id,
                                    "therapist_id": bundle.therapist_id,
                                    "error": "Failed to send email"
                                })
                        except Exception as e:
                            logger.error(f"Failed to send bundle {bundle.id}: {str(e)}")
                            send_errors.append({
                                "bundle_id": bundle.id,
                                "therapist_id": bundle.therapist_id,
                                "error": str(e)
                            })
                
                response = {
                    "message": f"Created {len(bundles)} bundles",
                    "buendel_erstellt": len(bundles),
                    "buendel_gesendet": sent_count,
                    "buendel_ids": [b.id for b in bundles]
                }
                
                if send_errors:
                    response["send_errors"] = send_errors
                
                return response, 201
                
        except Exception as e:
            logger.error(f"Bundle creation failed: {str(e)}", exc_info=True)
            return {
                "message": "Bundle creation failed",
                "error": str(e)
            }, 500


class BundleResponseResource(Resource):
    """REST resource for recording therapist responses to bundles."""

    def put(self, bundle_id):
        """Record a therapist's response to a bundle."""
        parser = reqparse.RequestParser()
        parser.add_argument('patient_responses', type=dict, required=True, location='json')
        parser.add_argument('notizen', type=str)
        parser.add_argument('follow_up_required', type=bool, default=False)
        args = parser.parse_args()
        
        try:
            with get_db() as db:
                # Validate bundle exists
                bundle = db.query(Therapeutenanfrage).filter_by(id=bundle_id).first()
                if not bundle:
                    return {"message": f"Bundle {bundle_id} not found"}, 404
                
                if not bundle.gesendet_datum:
                    return {"message": "Cannot record response for unsent bundle"}, 400
                
                # Validate patient responses
                patient_responses = {}
                for patient_id_str, outcome_str in args['patient_responses'].items():
                    try:
                        patient_id = int(patient_id_str)
                        outcome = PatientenErgebnis[outcome_str]
                        patient_responses[patient_id] = outcome
                    except (ValueError, KeyError):
                        valid_values = [o.value for o in PatientenErgebnis]
                        return {
                            "message": f"Invalid patient response: {patient_id_str} -> {outcome_str}",
                            "valid_outcomes": valid_values
                        }, 400
                
                # Verify all patients in bundle have responses
                bundle_patient_ids = {bp.patient_id for bp in bundle.bundle_patients}
                response_patient_ids = set(patient_responses.keys())
                
                missing_patients = bundle_patient_ids - response_patient_ids
                extra_patients = response_patient_ids - bundle_patient_ids
                
                if missing_patients:
                    return {
                        "message": "Missing responses for some patients",
                        "missing_patient_ids": list(missing_patients)
                    }, 400
                
                if extra_patients:
                    return {
                        "message": "Responses provided for patients not in bundle",
                        "extra_patient_ids": list(extra_patients)
                    }, 400
                
                # Handle the response
                old_response_type = bundle.antworttyp
                
                BundleService.handle_bundle_response(
                    db,
                    bundle_id=bundle_id,
                    patient_responses=patient_responses,
                    notes=args.get('notizen')
                )
                
                # Refresh bundle to get updated data
                db.refresh(bundle)
                
                # Set cooling period for therapist
                TherapistService.set_cooling_period(bundle.therapist_id)
                
                # Publish response event
                publish_bundle_response_received(
                    bundle.id,
                    bundle.antworttyp.value if bundle.antworttyp else None,
                    bundle.angenommen_anzahl,
                    bundle.abgelehnt_anzahl,
                    bundle.keine_antwort_anzahl
                )
                
                # Handle accepted patients
                accepted_patients = []
                for bp in bundle.bundle_patients:
                    if bp.is_accepted():
                        accepted_patients.append({
                            "patient_id": bp.patient_id,
                            "platzsuche_id": bp.platzsuche_id
                        })
                        
                        # Mark search as successful if patient accepted
                        search = db.query(Platzsuche).filter_by(id=bp.platzsuche_id).first()
                        if search and search.status == SuchStatus.aktiv:
                            search.mark_successful()
                            publish_search_status_changed(
                                search.id,
                                search.patient_id,
                                SuchStatus.aktiv.value,
                                SuchStatus.erfolgreich.value
                            )
                
                db.commit()
                
                return {
                    "message": "Bundle response recorded successfully",
                    "bundle_id": bundle.id,
                    "response_type": bundle.antworttyp.value if bundle.antworttyp else None,
                    "angenommene_patienten": accepted_patients,
                    "antwort_zusammenfassung": {
                        "accepted": bundle.angenommen_anzahl,
                        "rejected": bundle.abgelehnt_anzahl,
                        "no_response": bundle.keine_antwort_anzahl
                    }
                }, 200
                
        except IntegrityError as e:
            logger.error(f"Integrity error recording bundle response: {str(e)}")
            return {"message": "Data integrity error"}, 400
        except Exception as e:
            logger.error(f"Error recording bundle response: {str(e)}", exc_info=True)
            return {"message": "Internal server error"}, 500