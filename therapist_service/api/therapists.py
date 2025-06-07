"""Therapist API endpoints implementation."""
from datetime import datetime
from flask import request
from flask_restful import Resource, fields, marshal_with, reqparse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.dialects.postgresql import JSONB

from models.therapist import Therapist, TherapistStatus
from shared.utils.database import SessionLocal
from shared.api.base_resource import PaginatedListResource
from events.producers import (
    publish_therapist_created,
    publish_therapist_updated,
    publish_therapist_blocked,
    publish_therapist_unblocked
)


# Custom field for JSONB data
class JSONField(fields.Raw):
    """Field for JSON/JSONB data."""
    def format(self, value):
        """Return the JSON data as-is."""
        return value if value is not None else None


# Output fields definition for therapist responses - NOW WITH ALL GERMAN FIELDS
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
    'telefonische_erreichbarkeit': JSONField,
    'fremdsprachen': JSONField,
    'psychotherapieverfahren': JSONField,
    'zusatzqualifikationen': fields.String,
    'besondere_leistungsangebote': fields.String,
    # Contact History
    'letzter_kontakt_email': fields.String,  # Date as string
    'letzter_kontakt_telefon': fields.String,  # Date as string
    'letztes_persoenliches_gespraech': fields.String,  # Date as string
    # Availability (German field names)
    'potenziell_verfuegbar': fields.Boolean,
    'potenziell_verfuegbar_notizen': fields.String,
    # Bundle System Fields (German field names)
    'naechster_kontakt_moeglich': fields.String,  # Date as string
    'bevorzugte_diagnosen': JSONField,
    'alter_min': fields.Integer,
    'alter_max': fields.Integer,
    'geschlechtspraeferenz': fields.String,
    'arbeitszeiten': JSONField,
    'bevorzugt_gruppentherapie': fields.Boolean,
    # Status
    'status': fields.String,
    'sperrgrund': fields.String,
    'sperrdatum': fields.String,  # Date as string
    # Timestamps
    'created_at': fields.String,  # Date as string
    'updated_at': fields.String,  # Date as string
}


class TherapistResource(Resource):
    """REST resource for individual therapist operations."""

    @marshal_with(therapist_fields)
    def get(self, therapist_id):
        """Get a specific therapist by ID."""
        db = SessionLocal()
        try:
            therapist = db.query(Therapist).filter(
                Therapist.id == therapist_id
            ).first()
            if not therapist:
                return {'message': 'Therapist not found'}, 404
            return therapist
        except SQLAlchemyError as e:
            db.rollback()
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()

    @marshal_with(therapist_fields)
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
        parser.add_argument('telefonische_erreichbarkeit', type=dict)
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
            therapist = db.query(Therapist).filter(
                Therapist.id == therapist_id
            ).first()
            if not therapist:
                return {'message': 'Therapist not found'}, 404
            
            old_status = therapist.status
            
            # Update fields from request
            for key, value in args.items():
                if value is not None:
                    # Handle special fields
                    if key == 'status' and value:
                        # Handle enum conversion
                        therapist.status = TherapistStatus(value)
                    elif key in ['letzter_kontakt_email', 'letzter_kontakt_telefon', 
                                'letztes_persoenliches_gespraech', 'naechster_kontakt_moeglich', 
                                'sperrdatum']:
                        # Convert string dates to date objects
                        if value:
                            setattr(therapist, key, datetime.fromisoformat(value).date())
                    else:
                        setattr(therapist, key, value)
            
            db.commit()
            
            # Publish appropriate event based on status change
            therapist_data = {
                'vorname': therapist.vorname,
                'nachname': therapist.nachname,
                'anrede': therapist.anrede,
                'titel': therapist.titel,
                'email': therapist.email,
                'telefon': therapist.telefon,
                'status': therapist.status.value if therapist.status else None,
                'potenziell_verfuegbar': therapist.potenziell_verfuegbar,
                'naechster_kontakt_moeglich': str(therapist.naechster_kontakt_moeglich) if therapist.naechster_kontakt_moeglich else None
            }
            
            # Check for status changes to publish specific events
            if old_status != therapist.status:
                if therapist.status == TherapistStatus.BLOCKED:
                    publish_therapist_blocked(
                        therapist.id,
                        therapist_data,
                        therapist.sperrgrund
                    )
                elif (old_status == TherapistStatus.BLOCKED and
                      therapist.status == TherapistStatus.ACTIVE):
                    publish_therapist_unblocked(therapist.id, therapist_data)
                else:
                    publish_therapist_updated(therapist.id, therapist_data)
            else:
                publish_therapist_updated(therapist.id, therapist_data)
            
            return therapist
        except SQLAlchemyError as e:
            db.rollback()
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()

    def delete(self, therapist_id):
        """Delete a therapist."""
        db = SessionLocal()
        try:
            therapist = db.query(Therapist).filter(
                Therapist.id == therapist_id
            ).first()
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

    @marshal_with(therapist_fields)
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
                query = query.filter(Therapist.status == TherapistStatus(status))
            if potenziell_verfuegbar is not None:
                query = query.filter(Therapist.potenziell_verfuegbar == potenziell_verfuegbar)
            
            # Apply pagination
            query = self.paginate_query(query)
            
            # Get results
            therapists = query.all()
            return therapists
        except SQLAlchemyError as e:
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()

    @marshal_with(therapist_fields)
    def post(self):
        """Create a new therapist."""
        parser = reqparse.RequestParser()
        # Required fields
        parser.add_argument('vorname', type=str, required=True,
                           help='Vorname is required')
        parser.add_argument('nachname', type=str, required=True,
                           help='Nachname is required')
        # Personal Information (optional)
        parser.add_argument('anrede', type=str)
        parser.add_argument('titel', type=str)
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
            # Create new therapist
            therapist = Therapist(
                vorname=args['vorname'],
                nachname=args['nachname']
            )
            
            # Set all other fields from args
            for key, value in args.items():
                if value is not None and key not in ['vorname', 'nachname']:
                    # Handle special fields
                    if key == 'status' and value:
                        therapist.status = TherapistStatus(value)
                    elif key in ['letzter_kontakt_email', 'letzter_kontakt_telefon', 
                                'letztes_persoenliches_gespraech', 'naechster_kontakt_moeglich', 
                                'sperrdatum']:
                        # Convert string dates to date objects
                        if value:
                            setattr(therapist, key, datetime.fromisoformat(value).date())
                    else:
                        setattr(therapist, key, value)
            
            # Set defaults
            if therapist.kassensitz is None:
                therapist.kassensitz = True
            
            db.add(therapist)
            db.commit()
            db.refresh(therapist)
            
            # Publish event for therapist creation
            therapist_data = {
                'vorname': therapist.vorname,
                'nachname': therapist.nachname,
                'anrede': therapist.anrede,
                'titel': therapist.titel,
                'email': therapist.email,
                'telefon': therapist.telefon,
                'status': therapist.status.value if therapist.status else None,
                'potenziell_verfuegbar': therapist.potenziell_verfuegbar
            }
            publish_therapist_created(therapist.id, therapist_data)
            
            return therapist, 201
        except SQLAlchemyError as e:
            db.rollback()
            return {'message': f'Database error: {str(e)}'}, 500
        finally:
            db.close()
