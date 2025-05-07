"""Main application file for the Communication Service."""
from flask import Flask
from flask_restful import Api

from api.emails import EmailResource, EmailListResource
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
    
    # Register API endpoints for phone calls
    api.add_resource(PhoneCallListResource, '/api/phone-calls')
    api.add_resource(PhoneCallResource, '/api/phone-calls/<int:call_id>')
    api.add_resource(PhoneCallBatchResource, '/api/phone-call-batches/<int:batch_id>')

    # Start Kafka consumers
    start_consumers()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8004, debug=True)