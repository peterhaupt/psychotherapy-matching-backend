"""Main application file for the Communication Service."""
import os
import threading
from flask import Flask
from flask_restful import Api, Resource
from flask_cors import CORS

from api.emails import EmailResource, EmailListResource
from api.phone_calls import PhoneCallResource, PhoneCallListResource
from api.system_messages import SystemMessageResource
from shared.config import get_config, setup_logging
# NEW: Import the email queue processor
from utils import start_email_queue_processor, EmailQueueStatus


class HealthCheckResource(Resource):
    """Health check endpoint for service monitoring."""
    
    def get(self):
        """Return health status of the communication service."""
        return {
            'status': 'healthy',
            'service': 'communication-service'
        }


class EmailQueueHealthCheckResource(Resource):
    """Health check endpoint for email queue monitoring."""
    
    def get(self):
        """Return health status of the email queue processor."""
        return EmailQueueStatus.get_health_status()


class EmailQueueStatusResource(Resource):
    """REST resource for email queue status monitoring."""
    
    def get(self):
        """Get the current email queue status."""
        return EmailQueueStatus.get_status()


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Get and validate configuration
    config = get_config()
    config.validate("communication")
    
    # Log configuration status (non-sensitive values only)
    app.logger.info(f"Configuration validated for communication service")
    app.logger.info(f"Flask Environment: {config.FLASK_ENV}")
    app.logger.info(f"Database: {config.DB_NAME}")

    # Configure CORS using centralized settings
    CORS(app, **config.get_cors_settings())

    # Configure database connection
    app.config["SQLALCHEMY_DATABASE_URI"] = config.get_database_uri()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Configure email settings from centralized config
    smtp_settings = config.get_smtp_settings()
    app.config["SMTP_HOST"] = smtp_settings["host"]
    app.config["SMTP_PORT"] = smtp_settings["port"]
    app.config["SMTP_USERNAME"] = smtp_settings["username"]
    app.config["SMTP_PASSWORD"] = smtp_settings["password"]
    app.config["SMTP_USE_TLS"] = smtp_settings["use_tls"]
    app.config["EMAIL_SENDER"] = smtp_settings["sender"]
    app.config["EMAIL_SENDER_NAME"] = smtp_settings["sender_name"]
    
    # Configure logging
    app.logger.setLevel(config.LOG_LEVEL)

    # Initialize RESTful API
    api = Api(app)

    # Register health check endpoints (at root level, not under /api)
    api.add_resource(HealthCheckResource, '/health')
    api.add_resource(EmailQueueHealthCheckResource, '/health/email-queue')

    # Register API endpoints for emails
    api.add_resource(EmailListResource, '/api/emails')
    api.add_resource(EmailResource, '/api/emails/<int:email_id>')
    
    # Register API endpoints for phone calls
    api.add_resource(PhoneCallListResource, '/api/phone-calls')
    api.add_resource(PhoneCallResource, '/api/phone-calls/<int:call_id>')
    
    # Register API endpoint for system messages
    api.add_resource(SystemMessageResource, '/api/system-messages')
    
    # NEW: Register email queue status endpoint
    api.add_resource(EmailQueueStatusResource, '/api/emails/queue-status')
    
    # NEW: Start email queue processing thread
    # IMPORTANT: Only start in the main worker process, not in the reloader process
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
        email_queue_thread = threading.Thread(
            target=start_email_queue_processor,
            daemon=True,
            name="EmailQueueProcessor"
        )
        email_queue_thread.start()
        app.logger.info("Email queue processor thread started")
    else:
        app.logger.info("Skipping email queue processor in reloader process")

    return app


if __name__ == "__main__":
    # Set up centralized logging
    setup_logging("communication-service")
    
    config = get_config()
    app = create_app()
    app.run(
        host="0.0.0.0", 
        port=config.COMMUNICATION_SERVICE_INTERNAL_PORT, 
        debug=config.FLASK_DEBUG