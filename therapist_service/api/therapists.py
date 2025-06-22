"""Therapist API endpoints implementation with German enum support."""
from flask import request, jsonify
from flask_restful import Resource, fields, marshal_with, reqparse, marshal
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import requests
import logging

from models.therapist import Therapist, TherapistStatus
from shared.utils.database import SessionLocal
from shared.api.base_resource import PaginatedListResource
from shared.config import get_config
from events.producers import (
    publish_therapist_created,
    publish_therapist_updated,
    publish_therapist_blocked,
    publish_therapist_unblocked
)

# Get configuration
config = get_config()


# Custom field for enum serialization
class EnumField(fields.Raw):
    """Custom field for enum serialization that returns the enum value."""
    def format(self, value):
        if value is None:
            return None
        # If it's an enum, return its value
        if hasattr(value, 'value'):
            return value.value
        # If it's already a string (e.g., from request), return as is
        return value


# Custom field for date serialization
class DateField(fields.Raw):
    """Custom field for date serialization."""
    def format(self, value):
        if value is None:
            return None
        if isinstance(value, str):
            return value
        # Format date as YYYY-MM-DD string
        return value.strftime('%Y-%m-%d')


# Complete output fields definition for therapist responses
therapist_fields = {
    'id': fields.Integer,
    # Personal Information
    'anrede': fields.String,
    'titel': fields.String,
    'vorname': fields.String,
    'nachname': fields.String,
    'strasse': fields.String,
    'plz': fields.String,
    'ort': fields.String,
    'telefon': fields.String,
    'fax': fields.String,
    'email': fields.String,
    'webseite': fields.String,
    # Professional Information
    'kassensitz': fields.Boolean,
    'geschlecht': fields.String,
    'telefonische_erreichbarkeit': fields.Raw,  # JSONB field
    'fremdsprachen': fields.Raw,  # JSONB field
    'psychotherapieverfahren': fields.Raw,  # JSONB field
    'zusatzqualifikationen': fields.String,
    'besondere_leistungsangebote': fields.String,
    # Contact History
    'letzter_kontakt_email': DateField,
    'letzter_kontakt_telefon': DateField,
    'letztes_persoenliches_gespraech': DateField,
    # Availability (German field names)
    'potenziell_verfuegbar': fields.Boolean,
    'potenziell_verfuegbar_notizen': fields.String,
    # NEW: Phase 2 field
    'ueber_curavani_informiert': fields.Boolean,
    # Bundle System Fields (German field names)
    'naechster_kontakt_moeglich': DateField,
    'bevorzugte_diagnosen': fields.Raw,  # JSONB field
    'alter_min': fields.Integer,
    'alter_max': fields.Integer,
    'geschlechtspraeferenz': fields.String,
    'arbeitszeiten': fields.Raw,  # JSONB field
    'bevorzugt_gruppentherapie': fields.Boolean,
    # Status
    'status': EnumField,
    'sperrgrund': fields.String,
    'sperrdatum': DateField,
    # Timestamps
    'created_at': DateField,
    'updated_at': DateField,
}


def validate_and_get_therapist_status(status_value: str) -> TherapistStatus:
    """Validate and return TherapistStatus enum.
    
    Args:
        status_value: German status value from request
        
    Returns:
        TherapistStatus enum
        
    Raises:
        ValueError: If status value is invalid
    """
    if not status_value:
        return None
    
    # With German enums, we can directly access by name since name == value
    try:
        return TherapistStatus[status_value]
    except KeyError:
        valid_values = [status.value for status in TherapistStatus]
        raise ValueError(f"Invalid status '{status_value}'. Valid values: {valid_values}")


def parse_date_field(date_string: str, field_name: str):
    """Parse date string and return date object.
    
    Args:
        date_string: Date in YYYY-MM-DD format
        field_name: Name of field for error messages
        
    Returns:
        date object
        
    Raises:
        ValueError: If date format is invalid
    """
    if not date_string:
        return None
    
    try:
        return datetime.strptime(date_string, '%Y-%m-%d').date()
    except ValueError:
        raise ValueError(f"Invalid date format for {field_name}. Use YYYY-MM-DD")


class TherapistResource(Resource):
    """REST resource for individual therapist operations."""

    def get(self, therapist_id):
        """Get a specific therapist by ID."""
        db = SessionLocal()
        try:
            therapist = db.query(Therapist).filter(Therapist.id == therapist_id).first()
            if not therapist:
                return {'message': 'Therapist not found'}, 404
            return marshal(therapist, therapist_fields)
        except SQLAlchemyError as e:
            db.rollback()
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()

    def put(self, therapist_id):
        """Update an existing therapist."""
        parser = reqparse.RequestParser()
        # Personal Information
        parser.add_argument('anrede', type=str)
        parser.add_argument('titel', type=str)
        parser.add_argument('vorname', type=str)
        parser.add_argument('nachname', type=str)
        parser.add_argument('strasse', type=str)
        parser.add_argument('plz', type=str)
        parser.add_argument('ort', type=str)
        parser.add_argument('telefon', type=str)
        parser.add_argument('fax', type=str)
        parser.add_argument('email', type=str)
        parser.add_argument('webseite', type=str)
        # Professional Information
        parser.add_argument('kassensitz', type=bool)
        parser.add_argument('geschlecht', type=str)
        parser.add_argument('telefonische_erreichbarkeit', type=dict, location='json')
        parser.add_argument('fremdsprachen', type=list, location='json')
        parser.add_argument('psychotherapieverfahren', type=list, location='json')
        parser.add_argument('zusatzqualifikationen', type=str)
        parser.add_argument('besondere_leistungsangebote', type=str)
        # Contact History
        parser.add_argument('letzter_kontakt_email', type=str)
        parser.add_argument('letzter_kontakt_telefon', type=str)
        parser.add_argument('letztes_persoenliches_gespraech', type=str)
        # Availability (German field names)
        parser.add_argument('potenziell_verfuegbar', type=bool)
        parser.add_argument('potenziell_verfuegbar_notizen', type=str)
        parser.add_argument('ueber_curavani_informiert', type=bool)
        # Bundle System Fields (German field names)
        parser.add_argument('naechster_kontakt_moeglich', type=str)
        parser.add_argument('bevorzugte_diagnosen', type=list, location='json')
        parser.add_argument('alter_min', type=int)
        parser.add_argument('alter_max', type=int)
        parser.add_argument('geschlechtspraeferenz', type=str)
        parser.add_argument('arbeitszeiten', type=dict, location='json')
        parser.add_argument('bevorzugt_gruppentherapie', type=bool)
        # Status
        parser.add_argument('status', type=str)
        parser.add_argument('sperrgrund', type=str)
        parser.add_argument('sperrdatum', type=str)
        
        args = parser.parse_args()
        
        db = SessionLocal()
        try:
            therapist = db.query(Therapist).filter(Therapist.id == therapist_id).first()
            if not therapist:
                return {'message': 'Therapist not found'}, 404
            
            old_status = therapist.status
            
            # Update fields from request
            for key, value in args.items():
                if value is not None:
                    if key == 'status':
                        try:
                            therapist.status = validate_and_get_therapist_status(value)
                        except ValueError as e:
                            return {'message': str(e)}, 400
                    elif key in ['letzter_kontakt_email', 'letzter_kontakt_telefon', 
                                'letztes_persoenliches_gespraech', 'naechster_kontakt_moeglich', 
                                'sperrdatum']:
                        try:
                            setattr(therapist, key, parse_date_field(value, key))
                        except ValueError as e:
                            return {'message': str(e)}, 400
                    else:
                        setattr(therapist, key, value)
            
            db.commit()
            db.refresh(therapist)
            
            # Publish appropriate event based on status change
            therapist_data = marshal(therapist, therapist_fields)
            
            # Check for status changes to publish specific events
            if old_status != therapist.status:
                if therapist.status == TherapistStatus.gesperrt:
                    publish_therapist_blocked(
                        therapist.id,
                        therapist_data,
                        therapist.sperrgrund
                    )
                elif (old_status == TherapistStatus.gesperrt and
                      therapist.status == TherapistStatus.aktiv):
                    publish_therapist_unblocked(therapist.id, therapist_data)
                else:
                    publish_therapist_updated(therapist.id, therapist_data)
            else:
                publish_therapist_updated(therapist.id, therapist_data)
            
            return marshal(therapist, therapist_fields)
        except SQLAlchemyError as e:
            db.rollback()
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()

    def delete(self, therapist_id):
        """Delete a therapist."""
        db = SessionLocal()
        try:
            therapist = db.query(Therapist).filter(Therapist.id == therapist_id).first()
            if not therapist:
                return {'message': 'Therapist not found'}, 404
            
            db.delete(therapist)
            db.commit()
            
            return {'message': 'Therapist deleted successfully'}, 200
        except SQLAlchemyError as e:
            db.rollback()
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()


class TherapistListResource(PaginatedListResource):
    """REST resource for therapist collection operations."""

    def get(self):
        """Get a list of therapists with optional filtering and pagination."""
        # Parse query parameters for filtering
        status = request.args.get('status')
        potenziell_verfuegbar = request.args.get('potenziell_verfuegbar', type=bool)
        
        db = SessionLocal()
        try:
            query = db.query(Therapist)
            
            # Apply filters if provided
            if status:
                try:
                    status_enum = validate_and_get_therapist_status(status)
                    query = query.filter(Therapist.status == status_enum)
                except ValueError:
                    # If status value not found, return empty result
                    return {
                        "data": [],
                        "page": 1,
                        "limit": self.DEFAULT_LIMIT,
                        "total": 0
                    }
            
            if potenziell_verfuegbar is not None:
                query = query.filter(Therapist.potenziell_verfuegbar == potenziell_verfuegbar)
            
            # Use the new helper method
            return self.create_paginated_response(query, marshal, therapist_fields)
            
        except SQLAlchemyError as e:
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()

    def post(self):
        """Create a new therapist."""
        parser = reqparse.RequestParser()
        # Required fields
        parser.add_argument('vorname', type=str, required=True,
                           help='Vorname is required')
        parser.add_argument('nachname', type=str, required=True,
                           help='Nachname is required')
        # Optional fields
        parser.add_argument('anrede', type=str)
        parser.add_argument('titel', type=str)
        parser.add_argument('strasse', type=str)
        parser.add_argument('plz', type=str)
        parser.add_argument('ort', type=str)
        parser.add_argument('telefon', type=str)
        parser.add_argument('fax', type=str)
        parser.add_argument('email', type=str)
        parser.add_argument('webseite', type=str)
        parser.add_argument('kassensitz', type=bool)
        parser.add_argument('geschlecht', type=str)
        parser.add_argument('telefonische_erreichbarkeit', type=dict, location='json')
        parser.add_argument('fremdsprachen', type=list, location='json')
        parser.add_argument('psychotherapieverfahren', type=list, location='json')
        parser.add_argument('zusatzqualifikationen', type=str)
        parser.add_argument('besondere_leistungsangebote', type=str)
        parser.add_argument('letzter_kontakt_email', type=str)
        parser.add_argument('letzter_kontakt_telefon', type=str)
        parser.add_argument('letztes_persoenliches_gespraech', type=str)
        parser.add_argument('potenziell_verfuegbar', type=bool)
        parser.add_argument('potenziell_verfuegbar_notizen', type=str)
        parser.add_argument('ueber_curavani_informiert', type=bool)
        parser.add_argument('naechster_kontakt_moeglich', type=str)
        parser.add_argument('bevorzugte_diagnosen', type=list, location='json')
        parser.add_argument('alter_min', type=int)
        parser.add_argument('alter_max', type=int)
        parser.add_argument('geschlechtspraeferenz', type=str)
        parser.add_argument('arbeitszeiten', type=dict, location='json')
        parser.add_argument('bevorzugt_gruppentherapie', type=bool)
        parser.add_argument('status', type=str)
        parser.add_argument('sperrgrund', type=str)
        parser.add_argument('sperrdatum', type=str)
        
        try:
            args = parser.parse_args()
        except Exception as e:
            # Format validation errors to match expected format
            if hasattr(e, 'data') and 'message' in e.data:
                # Extract field-specific errors
                errors = []
                for field, msg in e.data['message'].items():
                    errors.append(f"{field}: {msg}")
                return {'message': ' '.join(errors)}, 400
            return {'message': str(e)}, 400
        
        db = SessionLocal()
        try:
            # Create new therapist
            therapist_data = {}
            
            # Process each argument
            for key, value in args.items():
                if value is not None:
                    if key == 'status':
                        try:
                            therapist_data['status'] = validate_and_get_therapist_status(value)
                        except ValueError as e:
                            return {'message': str(e)}, 400
                    elif key in ['letzter_kontakt_email', 'letzter_kontakt_telefon', 
                                'letztes_persoenliches_gespraech', 'naechster_kontakt_moeglich', 
                                'sperrdatum']:
                        try:
                            therapist_data[key] = parse_date_field(value, key)
                        except ValueError as e:
                            return {'message': str(e)}, 400
                    else:
                        therapist_data[key] = value
            
            therapist = Therapist(**therapist_data)
            
            db.add(therapist)
            db.commit()
            db.refresh(therapist)
            
            # Publish event for therapist creation
            therapist_marshalled = marshal(therapist, therapist_fields)
            publish_therapist_created(therapist.id, therapist_marshalled)
            
            return therapist_marshalled, 201
        except SQLAlchemyError as e:
            db.rollback()
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()


class TherapistCommunicationResource(Resource):
    """REST resource for therapist communication history."""
    
    def get(self, therapist_id):
        """Get communication history for a therapist."""
        # Verify therapist exists
        db = SessionLocal()
        try:
            therapist = db.query(Therapist).filter(Therapist.id == therapist_id).first()
            if not therapist:
                return {'message': 'Therapist not found'}, 404
        finally:
            db.close()
        
        # Call communication service to get emails and calls
        comm_service_url = config.get_service_url('communication', internal=True)
        
        try:
            # Get emails
            email_response = requests.get(
                f"{comm_service_url}/api/emails",
                params={'therapist_id': therapist_id}
            )
            emails = email_response.json() if email_response.ok else []
            
            # Get phone calls
            call_response = requests.get(
                f"{comm_service_url}/api/phone-calls",
                params={'therapist_id': therapist_id}
            )
            phone_calls = call_response.json() if call_response.ok else []
            
            # Combine and sort by date
            all_communications = []
            
            # Add emails
            for email in emails:
                all_communications.append({
                    'type': 'email',
                    'id': email.get('id'),
                    'date': email.get('gesendet_am') or email.get('created_at'),
                    'subject': email.get('betreff'),
                    'status': email.get('status'),
                    'response_received': email.get('antwort_erhalten'),
                    'data': email
                })
            
            # Add phone calls
            for call in phone_calls:
                all_communications.append({
                    'type': 'phone_call',
                    'id': call.get('id'),
                    'date': f"{call.get('geplantes_datum')} {call.get('geplante_zeit')}",
                    'status': call.get('status'),
                    'outcome': call.get('ergebnis'),
                    'data': call
                })
            
            # Sort by date (newest first)
            all_communications.sort(key=lambda x: x['date'] or '', reverse=True)
            
            # Get last contact date from therapist record
            last_email = therapist.letzter_kontakt_email.isoformat() if therapist.letzter_kontakt_email else None
            last_phone = therapist.letzter_kontakt_telefon.isoformat() if therapist.letzter_kontakt_telefon else None
            
            # Determine most recent contact
            last_contact = None
            if last_email and last_phone:
                last_contact = max(last_email, last_phone)
            else:
                last_contact = last_email or last_phone
            
            return {
                'therapist_id': therapist_id,
                'therapist_name': f"{therapist.titel or ''} {therapist.vorname} {therapist.nachname}".strip(),
                'last_contact': last_contact,
                'total_emails': len(emails),
                'total_calls': len(phone_calls),
                'communications': all_communications
            }
            
        except Exception as e:
            logging.error(f"Error fetching communication history: {str(e)}")
            return {'message': f'Error fetching communication history: {str(e)}'}, 500