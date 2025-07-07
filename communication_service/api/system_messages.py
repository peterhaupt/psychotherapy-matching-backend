"""System message API endpoint for internal notifications."""
import logging
from flask import request
from flask_restful import Resource

from utils.email_sender import send_email
from shared.config import get_config

logger = logging.getLogger(__name__)
config = get_config()


class SystemMessageResource(Resource):
    """REST resource for sending system messages/notifications."""
    
    def post(self):
        """Send a system notification email directly without database storage.
        
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
        
        try:
            # Convert plain text message to simple HTML
            html_message = f"<pre>{data['message']}</pre>"
            
            # Send email directly without storing in database
            success = send_email(
                to_email=recipient_email,
                subject=data['subject'],
                body_html=html_message,
                body_text=data['message'],
                sender_email=config.EMAIL_SENDER,
                sender_name=sender_name
            )
            
            if success:
                logger.info(f"System message sent successfully: {data['subject']}")
                return {
                    'message': 'System message sent successfully',
                    'recipient': recipient_email
                }, 200
            else:
                logger.error(f"Failed to send system message: {data['subject']}")
                return {
                    'message': 'Failed to send system message',
                    'recipient': recipient_email
                }, 500
                
        except Exception as e:
            logger.error(f"Error sending system message: {str(e)}", exc_info=True)
            return {'message': f'Error sending system message: {str(e)}'}, 500