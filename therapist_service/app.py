"""Main application file for the Therapist Service."""
import os
import threading
from flask import Flask, jsonify
from flask_restful import Api, Resource
from flask_cors import CORS

from api.therapists import TherapistResource, TherapistListResource, TherapistCommunicationResource, TherapistImportStatusResource
from shared.config import get_config, setup_logging
# NEW: Import the therapist import monitor
from imports import start_therapist_import_monitor


class HealthCheckResource(Resource):
    """Health check endpoint for service monitoring."""
    
    def get(self):
        """Return health status of the therapist service."""
        return {
            'status': 'healthy',
            'service': 'therapist-service'
        }


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Get and validate configuration
    config = get_config()
    config.validate("therapist")
    
    # Log configuration status (non-sensitive values only)
    app.logger.info(f"Configuration validated for therapist service")
    app.logger.info(f"Flask Environment: {config.FLASK_ENV}")
    app.logger.info(f"Database: {config.DB_NAME}")

    # Configure CORS using centralized settings
    CORS(app, **config.get_cors_settings())

    # Configure database connection
    app.config["SQLALCHEMY_DATABASE_URI"] = config.get_database_uri()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Configure logging
    app.logger.setLevel(config.LOG_LEVEL)

    # Initialize RESTful API
    api = Api(app)

    # Register health check endpoint (at root level, not under /api)
    api.add_resource(HealthCheckResource, '/health')

    # Register API endpoints
    api.add_resource(TherapistListResource, '/api/therapists')
    api.add_resource(TherapistResource, '/api/therapists/<int:therapist_id>')
    
    # Communication history endpoint
    api.add_resource(TherapistCommunicationResource, 
                     '/api/therapists/<int:therapist_id>/communication')
    
    # Import status endpoint
    api.add_resource(TherapistImportStatusResource, 
                     '/api/therapists/import-status')
    
    # Start therapist import monitoring thread
    # IMPORTANT: Only start in the main worker process, not in the reloader process
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
        therapist_import_thread = threading.Thread(
            target=start_therapist_import_monitor, 
            daemon=True,
            name="TherapistImportMonitor"
        )
        therapist_import_thread.start()
        app.logger.info("Therapist import monitor thread started")
    else:
        app.logger.info("Skipping therapist import monitor in reloader process")

    return app


if __name__ == "__main__":
    # Set up centralized logging
    setup_logging("therapist-service")
    
    config = get_config()
    app = create_app()
    app.run(
        host="0.0.0.0", 
        port=8002, 
        debug=config.FLASK_DEBUG
    )