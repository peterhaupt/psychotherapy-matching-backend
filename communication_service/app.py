"""Main application file for the Communication Service."""
from flask import Flask
from flask_restful import Api

from api.emails import (
    EmailResource, EmailListResource,
    EmailBatchListResource, EmailBatchResource
)
from api.phone_calls import (
    PhoneCallResource, 
    PhoneCallListResource, 
    PhoneCallBatchResource
)
from events.consumers import start_consumers
import config


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Configure database connection
    app.config["SQLALCHEMY_DATABASE_URI"] = config.DATABASE_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Configure email settings from config file
    app.config["SMTP_HOST"] = config.SMTP_HOST
    app.config["SMTP_PORT"] = config.SMTP_PORT
    app.config["SMTP_USERNAME"] = config.SMTP_USERNAME
    app.config["SMTP_PASSWORD"] = config.SMTP_PASSWORD
    app.config["SMTP_USE_TLS"] = config.SMTP_USE_TLS
    app.config["EMAIL_SENDER"] = config.EMAIL_SENDER
    app.config["EMAIL_SENDER_NAME"] = config.EMAIL_SENDER_NAME

    # Initialize RESTful API
    api = Api(app)

    # Register API endpoints for emails
    api.add_resource(EmailListResource, '/api/emails')
    api.add_resource(EmailResource, '/api/emails/<int:email_id>')
    api.add_resource(EmailBatchListResource, '/api/emails/<int:email_id>/batches')
    api.add_resource(EmailBatchResource, '/api/email-batches/<int:batch_id>')
    
    # Register API endpoints for phone calls
    api.add_resource(PhoneCallListResource, '/api/phone-calls')
    api.add_resource(PhoneCallResource, '/api/phone-calls/<int:call_id>')
    api.add_resource(PhoneCallBatchResource, '/api/phone-call-batches/<int:batch_id>')

    # Start Kafka consumers
    start_consumers()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8004, debug=config.DEBUG)