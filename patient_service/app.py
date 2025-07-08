"""Main application file for the Patient Service."""
import os
import threading
import time
from flask import Flask, jsonify
from flask_restful import Api
from flask_cors import CORS

from api.patients import PatientResource, PatientListResource, PatientCommunicationResource, PatientImportStatusResource
from shared.config import get_config, setup_logging
# PHASE 2: Import start_consumers
from events.consumers import start_consumers
# NEW: Import the patient import monitor
from imports import start_patient_import_monitor


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Get configuration
    config = get_config()

    # Configure CORS using centralized settings
    CORS(app, **config.get_cors_settings())

    # Configure database connection
    app.config["SQLALCHEMY_DATABASE_URI"] = config.get_database_uri()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Configure logging
    app.logger.setLevel(config.LOG_LEVEL)

    # Initialize RESTful API
    api = Api(app)

    # Register API endpoints
    api.add_resource(PatientListResource, '/api/patients')
    api.add_resource(PatientResource, '/api/patients/<int:patient_id>')
    
    # NEW: Register communication history endpoint
    api.add_resource(PatientCommunicationResource, 
                     '/api/patients/<int:patient_id>/communication')
    
    # NEW: Register import status endpoint
    api.add_resource(PatientImportStatusResource, 
                     '/api/patients/import-status')
    
    # PHASE 2: Start Kafka consumers for event-driven updates
    start_consumers()
    
    # NEW: Start patient import monitoring thread
    # IMPORTANT: Only start in the main worker process, not in the reloader process
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
        import_thread = threading.Thread(
            target=start_patient_import_monitor,
            daemon=True,
            name="PatientImportMonitor"
        )
        import_thread.start()
        app.logger.info("Patient import monitor thread started")
    else:
        app.logger.info("Skipping patient import monitor in reloader process")
    
    return app


if __name__ == "__main__":
    # Set up centralized logging
    setup_logging("patient-service")
    
    config = get_config()
    app = create_app()
    
    # Log Flask debug mode status
    app.logger.info(f"Flask Debug Mode: {config.FLASK_DEBUG}")
    app.logger.info(f"Flask Environment: {config.FLASK_ENV}")
    
    app.run(
        host="0.0.0.0", 
        port=config.PATIENT_SERVICE_PORT, 
        debug=config.FLASK_DEBUG
    )