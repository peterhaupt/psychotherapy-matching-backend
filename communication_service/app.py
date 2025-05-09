"""Main application file for the Communication Service."""
from flask import Flask, jsonify, request
from flask_restful import Api

from api.emails import (
    EmailResource, EmailListResource,
    EmailResponseResource, EmailBatchListResource, EmailBatchResource
)
from api.phone_calls import (
    PhoneCallResource, 
    PhoneCallListResource, 
    PhoneCallBatchResource
)
from events.consumers import start_consumers


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Configure database connection
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "postgresql://boona:boona_password@pgbouncer:6432/therapy_platform"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Add these lines to enable full error reporting
    app.config["DEBUG"] = True
    app.config["PROPAGATE_EXCEPTIONS"] = True
    app.config["PRESERVE_CONTEXT_ON_EXCEPTION"] = True
    
    # Configure email settings - using your local SMTP gateway
    app.config["SMTP_HOST"] = "127.0.0.1"
    app.config["SMTP_PORT"] = 1025
    app.config["SMTP_USERNAME"] = "therapieplatz@peterhaupt.de"
    app.config["SMTP_PASSWORD"] = "***REMOVED_EXPOSED_PASSWORD***"
    app.config["SMTP_USE_TLS"] = True
    app.config["EMAIL_SENDER"] = "therapieplatz@peterhaupt.de"
    app.config["EMAIL_SENDER_NAME"] = "Boona Therapieplatz-Vermittlung"

    # Initialize RESTful API
    api = Api(app)

    # Register API endpoints for emails
    api.add_resource(EmailListResource, '/api/emails')
    api.add_resource(EmailResource, '/api/emails/<int:email_id>')
    api.add_resource(EmailResponseResource, '/api/emails/<int:email_id>/response')
    api.add_resource(EmailBatchListResource, '/api/emails/<int:email_id>/batches')
    api.add_resource(EmailBatchResource, '/api/email-batches/<int:batch_id>')
    
    # Register API endpoints for phone calls
    api.add_resource(PhoneCallListResource, '/api/phone-calls')
    api.add_resource(PhoneCallResource, '/api/phone-calls/<int:call_id>')
    api.add_resource(PhoneCallBatchResource, '/api/phone-call-batches/<int:batch_id>')

    # Diagnostic endpoint for debugging email creation
    @app.route('/api/debug/create-email', methods=['POST'])
    def debug_email_creation():
        """Diagnostic endpoint to create an email with detailed error reporting."""
        try:
            from models.email import Email, EmailStatus
            from shared.utils.database import SessionLocal
            import datetime
            import logging
            
            # Log the incoming request
            logging.info(f"Request: {request.json}")
            
            db = SessionLocal()
            
            # Create email from request data
            data = request.json
            email = Email(
                therapist_id=data.get('therapist_id', 3),
                subject=data.get('subject', 'Debug Email'),
                body_html=data.get('body_html', '<p>Test Body</p>'),
                body_text=data.get('body_text', 'Test Body'),
                recipient_email=data.get('recipient_email', 'test@example.com'),
                recipient_name=data.get('recipient_name', 'Test User'),
                sender_email=data.get('sender_email', 'therapieplatz@peterhaupt.de'),
                sender_name=data.get('sender_name', 'Boona Therapieplatz-Vermittlung'),
            )
            
            # Log the email object before saving
            logging.info(f"Email object created: {email.__dict__}")
            
            # Add to database
            db.add(email)
            
            # Log status
            logging.info(f"Status type: {type(email.status)}")
            logging.info(f"Status value: {email.status}")
            
            # Commit to database
            db.commit()
            db.refresh(email)
            
            # Return success
            result = {
                'success': True,
                'email_id': email.id,
                'therapist_id': email.therapist_id,
                'subject': email.subject,
                'status': email.status.value if hasattr(email.status, 'value') else str(email.status),
                'status_type': str(type(email.status))
            }
            
            return jsonify(result), 201
            
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            logging.error(f"Error: {str(e)}\nTraceback: {error_traceback}")
            return jsonify({
                'success': False, 
                'error': str(e),
                'traceback': error_traceback
            }), 500
        finally:
            if 'db' in locals():
                db.close()

    # Start Kafka consumers
    start_consumers()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8004, debug=True)