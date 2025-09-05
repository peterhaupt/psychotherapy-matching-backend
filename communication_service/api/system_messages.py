"""System message API endpoint for internal notifications."""
import logging
from flask import request
from flask_restful import Resource

from utils.email_sender import send_email
from utils.markdown_processor import markdown_to_html, strip_html
from shared.config import get_config

logger = logging.getLogger(__name__)
config = get_config()


class SystemMessageResource(Resource):
    """REST resource for sending system messages/notifications."""
    
    def post(self):
        """Send a system notification email directly without database storage.
        
        Expected JSON body:
        {
            "subject": "Email Subject",
            "message": "Email content (plain text or markdown)",
            "sender_name": "Sender Name" (optional, defaults to "Curavani System"),
            "recipient_email": "email@example.com" (optional, defaults to SYSTEM_NOTIFICATION_EMAIL),
            "recipient_name": "Recipient Name" (optional, defaults to "Curavani Support"),
            "process_markdown": true/false (optional, defaults to false),
            "add_legal_footer": true/false (optional, defaults to false)
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
        
        # Get recipient details (with defaults)
        recipient_email = data.get('recipient_email', config.SYSTEM_NOTIFICATION_EMAIL)
        recipient_name = data.get('recipient_name', 'Curavani Support')
        sender_name = data.get('sender_name', 'Curavani System')
        
        # Process content based on options
        if data.get('process_markdown', False):
            # Process markdown to HTML
            try:
                html_message = markdown_to_html(data['message'])
                text_message = strip_html(html_message)
            except Exception as e:
                logger.error(f"Markdown processing failed: {str(e)}")
                # Fallback to simple formatting
                html_message = f"<pre>{data['message']}</pre>"
                text_message = data['message']
        else:
            # Simple HTML formatting
            html_message = f"<pre>{data['message']}</pre>"
            text_message = data['message']
        
        # Add legal footer if requested
        if data.get('add_legal_footer', False):
            try:
                # Import the function from emails module
                from api.emails import add_legal_footer
                html_message, text_message = add_legal_footer(html_message, text_message)
            except Exception as e:
                logger.warning(f"Failed to add legal footer: {str(e)}")
                # Continue without footer rather than failing
        
        try:
            # Send email directly without storing in database
            success = send_email(
                to_email=recipient_email,
                subject=data['subject'],
                body_html=html_message,
                body_text=text_message,
                sender_email=config.EMAIL_SENDER,
                sender_name=sender_name
            )
            
            if success:
                logger.info(f"System message sent successfully to {recipient_email}: {data['subject']}")
                return {
                    'message': 'System message sent successfully',
                    'recipient': recipient_email
                }, 200
            else:
                logger.error(f"Failed to send system message to {recipient_email}: {data['subject']}")
                return {
                    'message': 'Failed to send system message',
                    'recipient': recipient_email
                }, 500
                
        except Exception as e:
            logger.error(f"Error sending system message: {str(e)}", exc_info=True)
            return {'message': f'Error sending system message: {str(e)}'}, 500