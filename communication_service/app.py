"""Main application file for the Communication Service."""
from flask import Flask, jsonify
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

    # Register the test route - INSIDE create_app, not at module level
    @app.route('/api/test/email', methods=['POST'])
    def test_email_creation():
        """Test endpoint to create an email without Kafka events."""
        try:
            from models.email import Email, EmailStatus
            from shared.utils.database import SessionLocal
            import datetime
            
            db = SessionLocal()
            email = Email(
                therapist_id=3,  # Using the therapist we know exists
                subject="Test Email",
                body_html="<p>Test Body</p>",
                body_text="Test Body",
                recipient_email="test@example.com",
                recipient_name="Test User",
                sender_email="therapieplatz@peterhaupt.de",
                sender_name="Boona Therapieplatz-Vermittlung",
            )
            
            # Set the status using the enum VALUE directly, not the enum instance
            # This ensures SQLAlchemy uses 'entwurf' instead of 'DRAFT'
            email.status = "entwurf"  # EmailStatus.DRAFT.value
            
            db.add(email)
            db.commit()
            
            result = {
                'success': True,
                'email_id': email.id,
                'therapist_id': email.therapist_id,
                'subject': email.subject,
                'status': email.status.value if hasattr(email.status, 'value') else email.status
            }
            
            return jsonify(result), 201
            
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            return jsonify({
                'success': False, 
                'error': str(e),
                'traceback': error_traceback
            }), 500
        finally:
            db.close()

    # Start Kafka consumers
    start_consumers()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8004, debug=True)