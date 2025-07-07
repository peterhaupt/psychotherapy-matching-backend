"""System message API endpoint for internal notifications."""
import logging
from flask import request
from flask_restful import Resource
from datetime import datetime

from models.email import Email, EmailStatus
from shared.utils.database import SessionLocal
from shared.config import get_config

logger = logging.getLogger(__name__)
config = get_config()


class SystemMessageResource(Resource):
    """REST resource for sending system messages/notifications."""
    
    def post(self):
        """Send a system notification email.
        
        Expected JSON body:
        {
            "subject": "Import Error",
            "message": "Failed to import patient...",
            "sender_name": "Patient Import System" (optional)
        }
        """
        data = request.get_json()
        
        # Validate required fields
        if not data:
            return {'message': 'No data provided'}, 400
            
        if 'subject' not in data:
            return {'message': 'Subject is required'}, 400
            
        if 'message' not in data:
            return {'message': 'Message is required'}, 400
        
        # Get system notification email from config
        recipient_email = config.SYSTEM_NOTIFICATION_EMAIL
        sender_name = data.get('sender_name', 'Curavani System')
        
        db = SessionLocal()
        try:
            # Create simple text email with no patient/therapist ID
            email = Email(
                therapist_id=None,
                patient_id=None,
                betreff=data['subject'],
                inhalt_text=data['message'],
                inhalt_html=f"<pre>{data['message']}</pre>",  # Simple pre-formatted HTML
                empfaenger_email=recipient_email,
                empfaenger_name='Curavani Admin',
                absender_email=config.EMAIL_SENDER,
                absender_name=sender_name,
                status=EmailStatus.In_Warteschlange,  # Queue for immediate sending
                antwort_erhalten=False,
                wiederholungsanzahl=0
            )
            
            db.add(email)
            db.commit()
            db.refresh(email)
            
            logger.info(f"System message created: {email.id} - {data['subject']}")
            
            return {
                'message': 'System message queued successfully',
                'email_id': email.id,
                'recipient': recipient_email
            }, 201
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating system message: {str(e)}", exc_info=True)
            return {'message': f'Error creating system message: {str(e)}'}, 500
        finally:
            db.close()
