"""Anfrage system API endpoints - FULLY IMPLEMENTED."""
import logging
from datetime import datetime

from flask import request, jsonify
from flask_restful import Resource, reqparse
from sqlalchemy import and_, or_, desc
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from shared.api import PaginatedListResource
from shared.config import get_config
from db import get_db_context
from models import Platzsuche, Therapeutenanfrage, TherapeutAnfragePatient
from models.platzsuche import SuchStatus
from models.therapeutenanfrage import AntwortTyp
from models.therapeut_anfrage_patient import AnfragePatientStatus, PatientenErgebnis
from services import AnfrageService, PatientService, TherapistService
# REMOVED: Kafka event producers imports

from algorithms.anfrage_creator import (
    get_therapists_for_selection,
    create_anfrage_for_therapist
)

logger = logging.getLogger(__name__)

# Get configuration
config = get_config()


def validate_patient_data_for_platzsuche(patient_data: dict) -> tuple:
    """Validate that patient has all required fields for platzsuche creation.
    
    Args:
        patient_data: Patient data dictionary
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Required string fields that must not be empty/whitespace
    required_string_fields = [
        'geschlecht',
        'symptome',
        'krankenkasse',
        'geburtsdatum'
    ]
    
    # Required boolean fields that must be explicitly set
    required_boolean_fields = [
        'erfahrung_mit_psychotherapie',
        'offen_fuer_gruppentherapie'
    ]
    
    # Check string fields
    for field in required_string_fields:
        value = patient_data.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            return False, f"Patient field '{field}' is required and cannot be empty"
    
    # Check boolean fields
    for field in required_boolean_fields:
        value = patient_data.get(field)
        if value is None:
            return False, f"Patient field '{field}' must be explicitly set (true/false)"
    
    # Check zeitliche_verfuegbarkeit - must have at least one entry
    zeitliche = patient_data.get('zeitliche_verfuegbarkeit')
    if not zeitliche or not isinstance(zeitliche, dict):
        return False, "Patient must have 'zeitliche_verfuegbarkeit' with at least one day/time"
    
    # Check if at least one day has time slots
    has_availability = False
    for day, times in zeitliche.items():
        if times and isinstance(times, list) and len(times) > 0:
            # Check if times are not empty strings
            for time_slot in times:
                if time_slot and str(time_slot).strip():
                    has_availability = True
                    break
            if has_availability:
                break
    
    if not has_availability:
        return False, "Patient must have at least one valid time slot in 'zeitliche_verfuegbarkeit'"
    
    # Check conditional field
    if patient_data.get('erfahrung_mit_psychotherapie') is True:
        letzte_sitzung = patient_data.get('letzte_sitzung_vorherige_psychotherapie')
        if letzte_sitzung is None or (isinstance(letzte_sitzung, str) and not letzte_sitzung.strip()):
            return False, "Field 'letzte_sitzung_vorherige_psychotherapie' is required when 'erfahrung_mit_psychotherapie' is true"
    
    return True, None


class PlatzsucheResource(Resource):
    """REST resource for individual patient search operations."""

    def get(self, search_id):
        """Get a specific patient search by ID."""
        try:
            with get_db_context() as db:
                search = db.query(Platzsuche).filter_by(id=search_id).first()
                
                if not search:
                    return {"message": f"Patient search {search_id} not found"}, 404
                
                # Get patient data from Patient Service
                patient_data = PatientService.get_patient(search.patient_id)
                if not patient_data:
                    logger.warning(f"Could not fetch patient data for patient_id {search.patient_id}")
                
                # Get anfrage history
                anfrage_entries = []
                for entry in search.anfrage_entries:
                    anfrage = entry.therapeutenanfrage
                    therapist = TherapistService.get_therapist(anfrage.therapist_id)
                    
                    anfrage_entries.append({
                        "anfrage_id": anfrage.id,
                        "therapist_id": anfrage.therapist_id,
                        "therapeuten_name": f"{therapist.get('vorname', '')} {therapist.get('nachname', '')}" if therapist else "Unknown",
                        "position": entry.position_in_anfrage,
                        "status": entry.status.value,
                        "outcome": entry.antwortergebnis.value if entry.antwortergebnis else None,
                        "sent_date": anfrage.gesendet_datum.isoformat() if anfrage.gesendet_datum else None,
                        "response_date": anfrage.antwort_datum.isoformat() if anfrage.antwort_datum else None
                    })
                
                return {
                    "id": search.id,
                    "patient_id": search.patient_id,
                    "patient": patient_data,
                    "status": search.status.value,
                    "created_at": search.created_at.isoformat(),
                    "updated_at": search.updated_at.isoformat() if search.updated_at else None,
                    "ausgeschlossene_therapeuten": search.ausgeschlossene_therapeuten,
                    "erfolgreiche_vermittlung_datum": search.erfolgreiche_vermittlung_datum.isoformat() if search.erfolgreiche_vermittlung_datum else None,
                    "notizen": search.notizen,
                    "aktive_anfragen": search.get_active_anfrage_count(),
                    "gesamt_anfragen": search.get_total_anfrage_count(),
                    "anfrage_verlauf": anfrage_entries
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
            with get_db_context() as db:
                search = db.query(Platzsuche).filter_by(id=search_id).first()
                
                if not search:
                    return {"message": f"Patient search {search_id} not found"}, 404
                
                old_status = search.status
                
                # Update fields
                if args.get('status'):
                    try:
                        new_status = SuchStatus[args['status']]
                        search.status = new_status
                        
                        # REMOVED: Kafka event publishing for status change
                        
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
        """Delete a patient search and all related records."""
        try:
            with get_db_context() as db:
                search = db.query(Platzsuche).filter_by(id=search_id).first()
                
                if not search:
                    return {"message": f"Patient search {search_id} not found"}, 404
                
                # Delete the search (cascade will delete related TherapeutAnfragePatient entries)
                db.delete(search)
                db.commit()
                
                logger.info(f"Deleted patient search {search_id} and related records")
                return {"message": "Patient search deleted successfully"}, 200
                
        except Exception as e:
            logger.error(f"Error deleting patient search: {str(e)}")
            return {"message": "Internal server error"}, 500


class PlatzsucheListResource(PaginatedListResource):
    """REST resource for patient search collection operations."""

    def get(self):
        """Get all patient searches with optional filtering."""
        parser = reqparse.RequestParser()
        parser.add_argument('status', type=str, location='args')
        parser.add_argument('patient_id', type=int, location='args')
        parser.add_argument('min_anfragen', type=int, location='args')
        parser.add_argument('max_anfragen', type=int, location='args')
        args = parser.parse_args()
        
        try:
            with get_db_context() as db:
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
                
                # Filter by anfrage count if specified
                if args.get('min_anfragen') is not None or args.get('max_anfragen') is not None:
                    filtered_searches = []
                    for s in searches:
                        anfrage_count = s.get_total_anfrage_count()
                        if args.get('min_anfragen') is not None and anfrage_count < args['min_anfragen']:
                            continue
                        if args.get('max_anfragen') is not None and anfrage_count > args['max_anfragen']:
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
                        "aktive_anfragen": s.get_active_anfrage_count(),
                        "gesamt_anfragen": s.get_total_anfrage_count(),
                        "ausgeschlossene_therapeuten_anzahl": len(s.ausgeschlossene_therapeuten) if s.ausgeschlossene_therapeuten else 0,
                        "offen_fuer_gruppentherapie": patients.get(s.patient_id, {}).get('offen_fuer_gruppentherapie', False)
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
            with get_db_context() as db:
                # Verify patient exists and has required data
                patient = PatientService.get_patient(args['patient_id'])
                if not patient:
                    return {"message": f"Patient {args['patient_id']} not found"}, 404
                
                # Validate patient data
                is_valid, error_message = validate_patient_data_for_platzsuche(patient)
                if not is_valid:
                    return {
                        "message": "Cannot create platzsuche: " + error_message,
                        "patient_id": args['patient_id']
                    }, 400
                
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
                search = AnfrageService.create_patient_search(
                    db,
                    patient_id=args['patient_id']
                )
                
                if args.get('notizen'):
                    search.add_note(args['notizen'], author="API")
                    db.commit()
                
                # REMOVED: Kafka event publishing for search creation
                
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
            with get_db_context() as db:
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


class TherapeutenZurAuswahlResource(Resource):
    """REST resource for therapist selection."""

    def get(self):
        """Get therapists for manual selection."""
        parser = reqparse.RequestParser()
        parser.add_argument('plz_prefix', type=str, required=True, location='args')
        args = parser.parse_args()
        
        plz_prefix = args['plz_prefix']
        
        # Get PLZ match digits from configuration
        anfrage_config = config.get_anfrage_config()
        plz_match_digits = anfrage_config['plz_match_digits']
        
        # Validate PLZ prefix using dynamic configuration
        if not plz_prefix or len(plz_prefix) != plz_match_digits or not plz_prefix.isdigit():
            return {"message": f"Invalid PLZ prefix. Must be exactly {plz_match_digits} digits."}, 400
        
        try:
            # Get database session and pass it to the function
            with get_db_context() as db:
                # Get filtered and sorted therapists - now passing db session
                therapists = get_therapists_for_selection(db, plz_prefix)
                
                return {
                    "plz_prefix": plz_prefix,
                    "total": len(therapists),
                    "data": [{
                        "id": t['id'],
                        "anrede": t.get('anrede'),
                        "titel": t.get('titel'),
                        "vorname": t.get('vorname'),
                        "nachname": t.get('nachname'),
                        "strasse": t.get('strasse'),
                        "plz": t.get('plz'),
                        "ort": t.get('ort'),
                        "telefon": t.get('telefon'),
                        "email": t.get('email'),
                        "potenziell_verfuegbar": t.get('potenziell_verfuegbar', False),
                        "ueber_curavani_informiert": t.get('ueber_curavani_informiert', False),
                        "naechster_kontakt_moeglich": t.get('naechster_kontakt_moeglich'),
                        "bevorzugte_diagnosen": t.get('bevorzugte_diagnosen', []),
                        "psychotherapieverfahren": t.get('psychotherapieverfahren', [])
                    } for t in therapists]
                }, 200
            
        except Exception as e:
            logger.error(f"Error fetching therapists for selection: {str(e)}")
            return {"message": "Internal server error"}, 500


class TherapeutenanfrageResource(Resource):
    """REST resource for individual anfrage operations."""

    def get(self, anfrage_id):
        """Get a specific anfrage by ID with full details."""
        try:
            with get_db_context() as db:
                anfrage = db.query(Therapeutenanfrage).filter_by(id=anfrage_id).first()
                
                if not anfrage:
                    return {"message": f"Anfrage {anfrage_id} not found"}, 404
                
                # Get therapist data
                therapist_data = TherapistService.get_therapist(anfrage.therapist_id)
                if not therapist_data:
                    logger.warning(f"Could not fetch therapist data for therapist_id {anfrage.therapist_id}")
                
                # Get patient details
                patients = []
                for ap in anfrage.anfrage_patients:
                    patient_data = PatientService.get_patient(ap.patient_id)
                    
                    # Get the platzsuche data
                    search = db.query(Platzsuche).filter_by(id=ap.platzsuche_id).first()
                    
                    patients.append({
                        "position": ap.position_in_anfrage,
                        "patient_id": ap.patient_id,
                        "patient": patient_data,
                        "platzsuche_id": ap.platzsuche_id,
                        "search_created_at": search.created_at.isoformat() if search else None,
                        "wartezeit_tage": (datetime.utcnow() - search.created_at).days if search else None,
                        "status": ap.status.value,
                        "antwortergebnis": ap.antwortergebnis.value if ap.antwortergebnis else None,
                        "antwortnotizen": ap.antwortnotizen
                    })
                
                # Sort patients by position
                patients.sort(key=lambda x: x['position'])
                
                # Calculate response summary
                response_summary = {
                    "total_accepted": anfrage.angenommen_anzahl,
                    "total_rejected": anfrage.abgelehnt_anzahl,
                    "total_no_response": anfrage.keine_antwort_anzahl,
                    "antwort_vollstaendig": anfrage.is_response_complete()
                }
                
                return {
                    "id": anfrage.id,
                    "therapist_id": anfrage.therapist_id,
                    "therapist": therapist_data,
                    "erstellt_datum": anfrage.erstellt_datum.isoformat(),
                    "gesendet_datum": anfrage.gesendet_datum.isoformat() if anfrage.gesendet_datum else None,
                    "antwort_datum": anfrage.antwort_datum.isoformat() if anfrage.antwort_datum else None,
                    "tage_seit_versand": anfrage.days_since_sent(),
                    "antworttyp": anfrage.antworttyp.value if anfrage.antworttyp else None,
                    "anfragegroesse": anfrage.anfragegroesse,
                    "antwort_zusammenfassung": response_summary,
                    "notizen": anfrage.notizen,
                    "email_id": anfrage.email_id,
                    "phone_call_id": anfrage.phone_call_id,
                    "patients": patients,
                    "nachverfolgung_erforderlich": anfrage.needs_follow_up()
                }, 200
                
        except Exception as e:
            logger.error(f"Error fetching anfrage {anfrage_id}: {str(e)}")
            return {"message": "Internal server error"}, 500

    def delete(self, anfrage_id):
        """Delete a therapeutenanfrage and all related records."""
        try:
            with get_db_context() as db:
                anfrage = db.query(Therapeutenanfrage).filter_by(id=anfrage_id).first()
                
                if not anfrage:
                    return {"message": f"Anfrage {anfrage_id} not found"}, 404
                
                # Delete the anfrage (cascade will delete related TherapeutAnfragePatient entries)
                db.delete(anfrage)
                db.commit()
                
                logger.info(f"Deleted therapeutenanfrage {anfrage_id} and related records")
                return {"message": "Therapeutenanfrage deleted successfully"}, 200
                
        except Exception as e:
            logger.error(f"Error deleting therapeutenanfrage: {str(e)}")
            return {"message": "Internal server error"}, 500


class TherapeutenanfrageListResource(PaginatedListResource):
    """REST resource for anfrage collection operations."""

    def get(self):
        """Get all anfragen with optional filtering."""
        parser = reqparse.RequestParser()
        parser.add_argument('therapist_id', type=int, location='args')
        parser.add_argument('versand_status', type=str, location='args')
        parser.add_argument('antwort_status', type=str, location='args')
        parser.add_argument('nachverfolgung_erforderlich', type=bool, location='args')
        parser.add_argument('min_size', type=int, location='args')
        parser.add_argument('max_size', type=int, location='args')
        args = parser.parse_args()
        
        try:
            with get_db_context() as db:
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
                    query = query.filter(Therapeutenanfrage.anfragegroesse >= args['min_size'])
                
                if args.get('max_size'):
                    query = query.filter(Therapeutenanfrage.anfragegroesse <= args['max_size'])
                
                # Order by creation date (newest first)
                query = query.order_by(desc(Therapeutenanfrage.erstellt_datum))
                
                # Apply pagination
                page, limit = self.get_pagination_params()
                total = query.count()
                query = self.paginate_query(query)
                
                anfragen = query.all()
                
                # Filter by nachverfolgung_erforderlich if specified
                if args.get('nachverfolgung_erforderlich') is not None:
                    # Get follow-up threshold from config
                    follow_up_config = config.get_follow_up_config()
                    threshold_days = follow_up_config['threshold_days']
                    
                    anfragen = [a for a in anfragen if a.needs_follow_up(threshold_days) == args['nachverfolgung_erforderlich']]
                    if args['nachverfolgung_erforderlich']:
                        total = len(anfragen)  # Adjust total for filtered results
                
                # Get therapist data
                therapist_ids = list(set(a.therapist_id for a in anfragen))
                therapists = {}
                for tid in therapist_ids:
                    therapist_data = TherapistService.get_therapist(tid)
                    if therapist_data:
                        therapists[tid] = therapist_data
                
                # Get follow-up threshold from config for display
                follow_up_config = config.get_follow_up_config()
                threshold_days = follow_up_config['threshold_days']
                
                return {
                    "data": [{
                        "id": a.id,
                        "therapist_id": a.therapist_id,
                        "therapeuten_name": f"{therapists.get(a.therapist_id, {}).get('vorname', '')} {therapists.get(a.therapist_id, {}).get('nachname', '')}" if a.therapist_id in therapists else "Unknown",
                        "erstellt_datum": a.erstellt_datum.isoformat(),
                        "gesendet_datum": a.gesendet_datum.isoformat() if a.gesendet_datum else None,
                        "antwort_datum": a.antwort_datum.isoformat() if a.antwort_datum else None,
                        "tage_seit_versand": a.days_since_sent(),
                        "antworttyp": a.antworttyp.value if a.antworttyp else None,
                        "anfragegroesse": a.anfragegroesse,
                        "angenommen_anzahl": a.angenommen_anzahl,
                        "abgelehnt_anzahl": a.abgelehnt_anzahl,
                        "keine_antwort_anzahl": a.keine_antwort_anzahl,
                        "nachverfolgung_erforderlich": a.needs_follow_up(threshold_days),
                        "antwort_vollstaendig": a.is_response_complete()
                    } for a in anfragen],
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "summary": {
                        "total_anfragen": total,
                        "unsent_anfragen": sum(1 for a in anfragen if not a.gesendet_datum),
                        "pending_responses": sum(1 for a in anfragen if a.gesendet_datum and not a.antwort_datum),
                        "needing_follow_up": sum(1 for a in anfragen if a.needs_follow_up(threshold_days))
                    }
                }, 200
                
        except Exception as e:
            logger.error(f"Error fetching anfragen: {str(e)}")
            return {"message": "Internal server error"}, 500


class AnfrageCreationResource(Resource):
    """REST resource for creating anfragen for manually selected therapist."""

    def post(self):
        """Create anfrage for manually selected therapist."""
        parser = reqparse.RequestParser()
        parser.add_argument('therapist_id', type=int, required=True)
        parser.add_argument('plz_prefix', type=str, required=True)
        parser.add_argument('sofort_senden', type=bool, default=False)
        args = parser.parse_args()
        
        plz_prefix = args['plz_prefix']
        
        # Get PLZ match digits from configuration
        anfrage_config = config.get_anfrage_config()
        plz_match_digits = anfrage_config['plz_match_digits']
        
        # Validate PLZ prefix using dynamic configuration
        if not plz_prefix or len(plz_prefix) != plz_match_digits or not plz_prefix.isdigit():
            return {"message": f"Invalid PLZ prefix. Must be exactly {plz_match_digits} digits."}, 400
        
        try:
            with get_db_context() as db:
                # Create anfrage
                logger.info(f"Creating anfrage for therapist {args['therapist_id']} with PLZ prefix {plz_prefix}")
                
                anfrage = create_anfrage_for_therapist(
                    db,
                    args['therapist_id'],
                    plz_prefix
                )
                
                if not anfrage:
                    return {
                        "message": "No eligible patients found for this therapist",
                        "therapist_id": args['therapist_id'],
                        "plz_prefix": plz_prefix
                    }, 200
                
                # Commit the anfrage
                db.commit()
                
                # REMOVED: Kafka event publishing for anfrage creation
                
                # Send anfrage if requested
                if args.get('sofort_senden'):
                    try:
                        result = AnfrageService.send_anfrage(db, anfrage.id)
                        if result["success"]:
                            # REMOVED: Kafka event publishing for anfrage sent
                            logger.info(f"Anfrage {anfrage.id} sent successfully")
                    except Exception as e:
                        logger.error(f"Failed to send anfrage {anfrage.id}: {str(e)}")
                
                patient_ids = [ap.patient_id for ap in anfrage.anfrage_patients]
                
                return {
                    "message": f"Created anfrage with {anfrage.anfragegroesse} patients",
                    "anfrage_id": anfrage.id,
                    "therapist_id": anfrage.therapist_id,
                    "anfragegroesse": anfrage.anfragegroesse,
                    "patient_ids": patient_ids,
                    "gesendet": bool(anfrage.gesendet_datum)
                }, 201
                
        except Exception as e:
            logger.error(f"Anfrage creation failed: {str(e)}", exc_info=True)
            return {
                "message": "Anfrage creation failed",
                "error": str(e)
            }, 500


class AnfrageResponseResource(Resource):
    """REST resource for recording therapist responses to anfragen."""

    def put(self, anfrage_id):
        """Record a therapist's response to an anfrage."""
        parser = reqparse.RequestParser()
        parser.add_argument('patient_responses', type=dict, required=True, location='json')
        parser.add_argument('notizen', type=str)
        parser.add_argument('follow_up_required', type=bool, default=False)
        args = parser.parse_args()
        
        try:
            with get_db_context() as db:
                # Validate anfrage exists
                anfrage = db.query(Therapeutenanfrage).filter_by(id=anfrage_id).first()
                if not anfrage:
                    return {"message": f"Anfrage {anfrage_id} not found"}, 404
                
                if not anfrage.gesendet_datum:
                    return {"message": "Cannot record response for unsent anfrage"}, 400
                
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
                
                # Verify all patients in anfrage have responses
                anfrage_patient_ids = {ap.patient_id for ap in anfrage.anfrage_patients}
                response_patient_ids = set(patient_responses.keys())
                
                missing_patients = anfrage_patient_ids - response_patient_ids
                extra_patients = response_patient_ids - anfrage_patient_ids
                
                if missing_patients:
                    return {
                        "message": "Missing responses for some patients",
                        "missing_patient_ids": list(missing_patients)
                    }, 400
                
                if extra_patients:
                    return {
                        "message": "Responses provided for patients not in anfrage",
                        "extra_patient_ids": list(extra_patients)
                    }, 400
                
                # Handle the response
                old_response_type = anfrage.antworttyp
                
                AnfrageService.handle_anfrage_response(
                    db,
                    anfrage_id=anfrage_id,
                    patient_responses=patient_responses,
                    notes=args.get('notizen')
                )
                
                # Refresh anfrage to get updated data
                db.refresh(anfrage)
                
                # Set cooling period for therapist
                TherapistService.set_cooling_period(anfrage.therapist_id)
                
                # REMOVED: Kafka event publishing for response received
                
                # Handle accepted patients
                accepted_patients = []
                for ap in anfrage.anfrage_patients:
                    if ap.is_accepted():
                        accepted_patients.append({
                            "patient_id": ap.patient_id,
                            "platzsuche_id": ap.platzsuche_id
                        })
                        
                        # Mark search as successful if patient accepted
                        search = db.query(Platzsuche).filter_by(id=ap.platzsuche_id).first()
                        if search and search.status == SuchStatus.aktiv:
                            search.mark_successful()
                            # REMOVED: Kafka event publishing for search status change
                
                db.commit()
                
                return {
                    "message": "Anfrage response recorded successfully",
                    "anfrage_id": anfrage.id,
                    "response_type": anfrage.antworttyp.value if anfrage.antworttyp else None,
                    "angenommene_patienten": accepted_patients,
                    "antwort_zusammenfassung": {
                        "accepted": anfrage.angenommen_anzahl,
                        "rejected": anfrage.abgelehnt_anzahl,
                        "no_response": anfrage.keine_antwort_anzahl
                    }
                }, 200
                
        except IntegrityError as e:
            logger.error(f"Integrity error recording anfrage response: {str(e)}")
            return {"message": "Data integrity error"}, 400
        except Exception as e:
            logger.error(f"Error recording anfrage response: {str(e)}", exc_info=True)
            return {"message": "Internal server error"}, 500


class AnfrageSendResource(Resource):
    """REST resource for sending an unsent anfrage."""
    
    def post(self, anfrage_id):
        """Send an anfrage via email or phone call."""
        try:
            with get_db_context() as db:
                anfrage = db.query(Therapeutenanfrage).filter_by(id=anfrage_id).first()
                
                if not anfrage:
                    return {"message": f"Anfrage {anfrage_id} not found"}, 404
                
                if anfrage.gesendet_datum:
                    return {
                        "message": "Anfrage already sent",
                        "sent_date": anfrage.gesendet_datum.isoformat()
                    }, 400
                
                # Send the anfrage (handles both email and phone call)
                result = AnfrageService.send_anfrage(db, anfrage.id)
                
                if result["success"]:
                    return {
                        "message": "Anfrage sent successfully",
                        "anfrage_id": anfrage.id,
                        "communication_type": result["communication_type"],
                        "email_id": result.get("email_id"),
                        "phone_call_id": result.get("phone_call_id"),
                        "sent_date": result["sent_date"].isoformat() if result["sent_date"] else None
                    }, 200
                else:
                    if result.get("error") == "Already sent":
                        return {
                            "message": "Anfrage already sent",
                            "sent_date": result["sent_date"].isoformat() if result.get("sent_date") else None
                        }, 400
                    else:
                        return {"message": f"Failed to send anfrage: {result.get('error', 'Unknown error')}"}, 500
                        
        except Exception as e:
            logger.error(f"Error sending anfrage {anfrage_id}: {str(e)}", exc_info=True)
            return {"message": "Internal server error"}, 500