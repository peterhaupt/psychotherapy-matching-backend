"""Main application file for the Communication Service."""
from flask import Flask
from flask_restful import Api, Resource
from flask_cors import CORS

from api.emails import EmailResource, EmailListResource
from api.phone_calls import PhoneCallResource, PhoneCallListResource
from api.system_messages import SystemMessageResource
from shared.config import get_config, setup_logging


class HealthCheckResource(Resource):
    """Health check endpoint for service monitoring."""
    
    def get(self):
        """Return health status of the communication service."""
        return {
            'status': 'healthy',
            'service': 'communication-service'
        }


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

    # Register health check endpoint (at root level, not under /api)
    api.add_resource(HealthCheckResource, '/health')

    # Register API endpoints for emails
    api.add_resource(EmailListResource, '/api/emails')
    api.add_resource(EmailResource, '/api/emails/<int:email_id>')
    
    # Register API endpoints for phone calls
    api.add_resource(PhoneCallListResource, '/api/phone-calls')
    api.add_resource(PhoneCallResource, '/api/phone-calls/<int:call_id>')
    
    # Register API endpoint for system messages
    api.add_resource(SystemMessageResource, '/api/system-messages')

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
    )